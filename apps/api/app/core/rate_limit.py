from math import ceil
from threading import Lock
from time import monotonic
from hashlib import sha256
import hmac
from ipaddress import ip_address, ip_network
from redis.asyncio import Redis
from redis.exceptions import RedisError
from starlette.responses import JSONResponse
from app.core.config import settings
from app.core.security import decode_access_token


class WindowLimiter:
    """Bounded, per-process MVP request limits. No forwarded IP header is trusted."""
    def __init__(self,clock=monotonic):
        self.clock=clock;self.buckets={};self.lock=Lock()

    def allow(self,key,limit):
        now=self.clock()
        with self.lock:
            start,count=self.buckets.get(key,(now,0))
            if now-start>=60:start,count=now,0
            if key not in self.buckets and len(self.buckets)>=10000:
                self.buckets={name:value for name,value in self.buckets.items() if now-value[0]<60}
                if len(self.buckets)>=10000:return False,60
            if count>=limit:return False,max(1,ceil(60-(now-start)))
            self.buckets[key]=(start,count+1)
            return True,0


RATE_SCRIPT = """
local count = redis.call('INCR', KEYS[1])
local ttl = redis.call('PTTL', KEYS[1])
if ttl < 0 then
    redis.call('PEXPIRE', KEYS[1], 60000)
    ttl = 60000
end
return {count, ttl}
"""


def client_address(scope):
    peer = (scope.get("client") or ("unknown", 0))[0]
    try:
        address = ip_address(peer)
        trusted = any(address in ip_network(network.strip(), strict=False)
                      for network in settings.trusted_proxy_ips.split(",") if network.strip())
        if trusted:
            value = dict(scope.get("headers", [])).get(b"x-mascomatch-client-ip", b"").decode("ascii")
            return ip_address(value).compressed
    except (ValueError, UnicodeError):
        pass
    return peer


def private_key(group, actor):
    digest = hmac.new(settings.jwt_secret.encode(), str(actor).encode(), sha256).hexdigest()
    return f"mascomatch:limits:{group}:{digest}"


class RedisWindowLimiter:
    def __init__(self):
        self.client = Redis.from_url(settings.redis_url, socket_connect_timeout=1, socket_timeout=1)

    async def allow(self, key, limit):
        count, ttl = await self.client.eval(RATE_SCRIPT, 1, private_key(*key))
        return int(count) <= limit, max(1, ceil(int(ttl) / 1000))


class RateLimitMiddleware:
    def __init__(self,app):
        self.app=app
        self.limiter=WindowLimiter()
        self.shared=None
    async def __call__(self,scope,receive,send):
        if scope["type"]!="http" or not settings.rate_limit_enabled or not scope.get("path","").startswith("/api/v1") or scope.get("method")=="OPTIONS":
            return await self.app(scope,receive,send)
        path=scope["path"];headers=dict(scope.get("headers",[]));actor=client_address(scope)
        group="auth" if path.startswith("/api/v1/auth/") and scope["method"]=="POST" else "read" if scope["method"] in {"GET","HEAD"} else "publish"
        authorization=headers.get(b"authorization",b"").decode("utf-8",errors="ignore")
        if group != "auth" and authorization.startswith("Bearer "):
            try:actor=str(decode_access_token(authorization[7:]))
            except Exception:pass
        limit=getattr(settings,f"rate_limit_{group}")
        if settings.rate_limit_backend == "redis":
            if self.shared is None:
                self.shared=RedisWindowLimiter()
            try:
                allowed,wait=await self.shared.allow((group,actor),limit)
            except (RedisError, OSError):
                if group != "read":
                    return await JSONResponse({"detail":"El servicio está temporalmente ocupado. Intentá de nuevo."}, status_code=503, headers={"Retry-After":"10"})(scope,receive,send)
                allowed,wait=self.limiter.allow((group,actor),limit)
        else:
            allowed,wait=self.limiter.allow((group,actor),limit)
        if not allowed:return await JSONResponse({"detail":"Demasiadas solicitudes. Esperá un momento e intentá de nuevo."},status_code=429,headers={"Retry-After":str(wait)})(scope,receive,send)
        return await self.app(scope,receive,send)
