"""Protect accounts without storing their addresses in Redis keys."""
from redis import Redis
from redis.exceptions import RedisError
from fastapi import HTTPException
from app.core.config import settings
from app.core.rate_limit import RATE_SCRIPT, private_key


def check_login_budget(email):
    if not settings.rate_limit_enabled or settings.rate_limit_backend != "redis":
        return
    try:
        with Redis.from_url(settings.redis_url, socket_connect_timeout=1, socket_timeout=1) as redis:
            count, ttl = redis.eval(RATE_SCRIPT, 1, private_key("login-account", email))
        if count > 6:
            raise HTTPException(status_code=429, detail="Esperá un momento antes de volver a ingresar.",
                                headers={"Retry-After": str(max(1, (ttl + 999) // 1000))})
    except (RedisError, OSError) as exc:
        raise HTTPException(status_code=503, detail="El acceso está temporalmente ocupado.", headers={"Retry-After":"10"}) from exc
