import asyncio
from contextlib import asynccontextmanager, suppress

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware

from app.core.config import settings
from app.core.rate_limit import RateLimitMiddleware
from app.core.observability import ObservabilityMiddleware
from app.routers import analysis, auth, dashboard, linked_sightings, lost_cases, map, matches, moderation, notifications, observations, operations, pets, photos, public_lost_dogs, reviews, upload_admission


@asynccontextmanager
async def lifespan(application: FastAPI):
    from app.matching.linked import reconciliation_loop
    from app.notifications.email import delivery_loop
    from app.matching.engine import general_matching_loop
    from app.account_mail import delivery_loop as account_delivery_loop
    tasks = [asyncio.create_task(reconciliation_loop()), asyncio.create_task(delivery_loop()), asyncio.create_task(general_matching_loop()),asyncio.create_task(account_delivery_loop())]
    if settings.ai_enabled or settings.embeddings_enabled:
        from app.analysis.queue import dispatch_loop
        tasks.append(asyncio.create_task(dispatch_loop()))
    try:
        yield
    finally:
        for task in tasks:
            task.cancel()
            with suppress(asyncio.CancelledError):
                await task

app = FastAPI(
    title="MascoMatch API",
    description="Mascotas, reportes y extracción de características de textos y fotos.",
    version="0.2.0",
    lifespan=lifespan,
    openapi_url=None if settings.app_env == "production" else "/api/v1/openapi.json",
    docs_url=None if settings.app_env == "production" else "/api/v1/docs",
    redoc_url=None,
)
app.add_middleware(RateLimitMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)
app.add_middleware(TrustedHostMiddleware, allowed_hosts=[value.strip() for value in settings.allowed_hosts.split(",") if value.strip()])
app.add_middleware(ObservabilityMiddleware)
app.include_router(auth.router, prefix="/api/v1")
app.include_router(pets.router, prefix="/api/v1")
app.include_router(lost_cases.router, prefix="/api/v1")
app.include_router(observations.router, prefix="/api/v1")
app.include_router(photos.router, prefix="/api/v1")
app.include_router(analysis.router, prefix="/api/v1")
app.include_router(public_lost_dogs.router, prefix="/api/v1")
app.include_router(public_lost_dogs.legacy_router, prefix="/api/v1")
app.include_router(linked_sightings.router, prefix="/api/v1")
app.include_router(notifications.router, prefix="/api/v1")
app.include_router(matches.router, prefix="/api/v1")
app.include_router(dashboard.router, prefix="/api/v1")
app.include_router(map.router, prefix="/api/v1")
app.include_router(moderation.router, prefix="/api/v1")
app.include_router(reviews.router, prefix="/api/v1")
app.include_router(operations.router)
app.include_router(upload_admission.router)


@app.get("/health", tags=["health"])
def health():
    return {"status": "ok"}

