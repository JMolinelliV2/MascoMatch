import asyncio
from contextlib import asynccontextmanager, suppress

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.routers import analysis, auth, linked_sightings, lost_cases, notifications, observations, pets, photos, public_lost_dogs


@asynccontextmanager
async def lifespan(application: FastAPI):
    from app.matching.linked import reconciliation_loop
    from app.notifications.email import delivery_loop
    tasks = [asyncio.create_task(reconciliation_loop()), asyncio.create_task(delivery_loop())]
    if settings.ai_enabled:
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
    title="PetMatch API",
    description="Mascotas, reportes y extracción de características de textos y fotos.",
    version="0.2.0",
    lifespan=lifespan,
    openapi_url="/api/v1/openapi.json",
    docs_url="/api/v1/docs",
    redoc_url=None,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)
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


@app.get("/health", tags=["health"])
def health():
    return {"status": "ok"}

