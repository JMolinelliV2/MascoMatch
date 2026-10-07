import asyncio
from contextlib import asynccontextmanager, suppress

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.routers import analysis, auth, lost_cases, observations, pets, photos


@asynccontextmanager
async def lifespan(application: FastAPI):
    task = None
    if settings.ai_enabled:
        from app.analysis.queue import dispatch_loop
        task = asyncio.create_task(dispatch_loop())
    try:
        yield
    finally:
        if task is not None:
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


@app.get("/health", tags=["health"])
def health():
    return {"status": "ok"}

