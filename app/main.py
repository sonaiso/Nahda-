from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.routes import router
from app.core.rate_limiter import RateLimitMiddleware
from app.db.session import init_db


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    yield


def create_app() -> FastAPI:
    app = FastAPI(
        title="Nahda Arabic Fractal Engine",
        version="0.1.0",
        description="MVP implementation of L0-L4 analysis pipeline.",
        lifespan=lifespan,
    )
    app.add_middleware(RateLimitMiddleware)
    app.include_router(router)
    app.include_router(router, prefix="/v1")

    return app


app = create_app()
