"""Request correlation without logging contacts, request bodies or URL queries."""
import json
import logging
from time import perf_counter
from uuid import uuid4
from redis.asyncio import Redis
from redis.exceptions import RedisError
from app.core.config import settings

logger = logging.getLogger("mascomatch.http")
logger.setLevel(logging.INFO)
if not logger.handlers:
    handler=logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(message)s"))
    logger.addHandler(handler)
logger.propagate=False


class ObservabilityMiddleware:
    def __init__(self, app):
        self.app = app
        self.redis = None

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)
        request_id, start, status = uuid4().hex, perf_counter(), 500

        async def response(message):
            nonlocal status
            if message["type"] == "http.response.start":
                status = message["status"]
                message["headers"] = [*message.get("headers", []), (b"x-request-id", request_id.encode())]
            await send(message)

        try:
            await self.app(scope, receive, response)
        finally:
            if settings.app_env == "production":
                route = getattr(scope.get("route"), "path", "/unmatched")
                method = scope.get("method") if scope.get("method") in {"GET", "HEAD", "POST", "PATCH", "DELETE", "OPTIONS"} else "OTHER"
                logger.info(json.dumps({"event":"http_request", "request_id":request_id, "route":route,
                                        "method":method, "status":status, "duration_ms":round((perf_counter()-start)*1000)}))
                if scope.get("path", "").startswith("/api/v1"):
                    try:
                        if self.redis is None:
                            self.redis = Redis.from_url(settings.redis_url, socket_connect_timeout=1, socket_timeout=1)
                        async with self.redis.pipeline(transaction=True) as pipe:
                            pipe.hincrby("mascomatch:metrics:http", f"{status // 100}xx", 1)
                            pipe.expire("mascomatch:metrics:http", 86400)
                            await pipe.execute()
                    except (RedisError, OSError):
                        pass
