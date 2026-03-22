import os
import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi import Request
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from app.api.router import api_router
from app.services.manual_preview_service import ManualPreviewService


def _allowed_origins() -> list[str]:
    configured = os.getenv("IPU_ALLOWED_ORIGINS", "").strip()
    if configured:
        return [origin.strip() for origin in configured.split(",") if origin.strip()]
    return [
        "http://localhost:4241",
        "http://127.0.0.1:4241",
    ]


limiter = Limiter(key_func=get_remote_address)


async def cleanup_expired_sessions(app: FastAPI):
    """Background task to cleanup expired sessions periodically."""
    while True:
        await asyncio.sleep(300)
        try:
            service = app.state.manual_preview_service
            if hasattr(service.session_store, "cleanup_expired_sessions"):
                service.session_store.cleanup_expired_sessions()
        except Exception:
            pass


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.manual_preview_service = ManualPreviewService()
    task = asyncio.create_task(cleanup_expired_sessions(app))
    yield
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass


def create_app() -> FastAPI:
    app = FastAPI(
        title="IPU AI Firewall Backend",
        description="Manual mode security replacement workbench API",
        version="0.1.0",
        lifespan=lifespan,
    )

    app.state.limiter = limiter

    @app.exception_handler(RateLimitExceeded)
    async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
        return {"detail": "Rate limit exceeded. Please try again later."}, 429

    app.add_middleware(
        CORSMiddleware,
        allow_origins=_allowed_origins(),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/")
    @limiter.limit("60/minute")
    async def root(request: Request) -> dict[str, str]:
        return {"status": "running", "service": "ipu-ai-firewall-backend"}

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "healthy", "mode": "manual-preview"}

    app.include_router(api_router)
    return app


app = create_app()
