from math import ceil
from threading import Lock
from time import monotonic
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


class RateLimitMiddleware:
    def __init__(self,app):self.app=app;self.limiter=WindowLimiter()
    async def __call__(self,scope,receive,send):
        if scope["type"]!="http" or not settings.rate_limit_enabled or not scope.get("path","").startswith("/api/v1") or scope.get("method")=="OPTIONS":
            return await self.app(scope,receive,send)
        path=scope["path"];headers=dict(scope.get("headers",[]));actor=(scope.get("client") or ("unknown",0))[0]
        authorization=headers.get(b"authorization",b"").decode("utf-8",errors="ignore")
        if authorization.startswith("Bearer "):
            try:actor=str(decode_access_token(authorization[7:]))
            except Exception:pass
        group="auth" if path in {"/api/v1/auth/login","/api/v1/auth/register"} else "read" if scope["method"] in {"GET","HEAD"} else "publish"
        allowed,wait=self.limiter.allow((group,actor),getattr(settings,f"rate_limit_{group}"))
        if not allowed:return await JSONResponse({"detail":"Demasiadas solicitudes. Esperá un momento e intentá de nuevo."},status_code=429,headers={"Retry-After":str(wait)})(scope,receive,send)
        return await self.app(scope,receive,send)
