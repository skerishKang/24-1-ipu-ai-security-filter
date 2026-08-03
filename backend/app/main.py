import asyncio
import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded

from app.api.router import api_router
from app.core.auth import API_KEY_HEADER_NAME
from app.core.rate_limit import limiter
from app.core.settings import get_settings, resolve_deployment_env, validate_public_api_key_hash
from app.services.manual_preview_service import ManualPreviewService

logger = logging.getLogger("uvicorn.error")


def _split_env_list(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


def _env_flag(name: str, default: bool = False) -> bool:
    configured = os.getenv(name)
    if configured is None:
        return default
    return configured.strip().lower() in {"1", "true", "yes", "on"}


def _deployment_stage() -> str:
    return resolve_deployment_env()


def _is_ops_stage() -> bool:
    return _deployment_stage() in {"ops-target", "production", "prod", "ops"}


def _allowed_origins() -> list[str]:
    configured = os.getenv("IPU_ALLOWED_ORIGINS", "").strip()
    if configured:
        return _split_env_list(configured)
    if _is_ops_stage():
        raise RuntimeError("IPU_ALLOWED_ORIGINS must be set for ops-target deployments")
    return [
        "http://localhost:4241",
        "http://127.0.0.1:4241",
    ]


def _cors_allow_credentials() -> bool:
    return _env_flag("IPU_CORS_ALLOW_CREDENTIALS", default=False)


def _cors_methods() -> list[str]:
    configured = os.getenv("IPU_CORS_ALLOW_METHODS", "").strip()
    if configured:
        return _split_env_list(configured)
    return ["GET", "POST"]


def _cors_headers() -> list[str]:
    configured = os.getenv("IPU_CORS_ALLOW_HEADERS", "").strip()
    if configured:
        return _split_env_list(configured)
    return ["Content-Type", API_KEY_HEADER_NAME]


async def cleanup_expired_sessions(app: FastAPI):
    """Background task to cleanup expired sessions periodically."""
    while True:
        await asyncio.sleep(300)
        try:
            service = app.state.manual_preview_service
            if hasattr(service.session_store, "cleanup_expired_sessions"):
                service.session_store.cleanup_expired_sessions()
        except Exception:
            logger.warning("manual_preview_session_cleanup_failed", exc_info=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.manual_preview_service = ManualPreviewService(settings=app.state.settings)
    task = asyncio.create_task(cleanup_expired_sessions(app))
    yield
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass


def create_app() -> FastAPI:
    settings = get_settings()
    validate_public_api_key_hash(settings.deployment_env, settings.api_key_hash)
    # Hide the OpenAPI surface in non-dev deployments. ``/docs``, ``/redoc``
    # and ``/openapi.json`` would otherwise leak field names, the API key
    # header, and request constraints to anyone who can reach the server.
    public = settings.is_public_deployment()
    app = FastAPI(
        title="IPU AI Firewall Backend",
        description="Manual mode security replacement workbench API",
        version="0.1.0",
        lifespan=lifespan,
        docs_url=None if public else "/docs",
        redoc_url=None if public else "/redoc",
        openapi_url=None if public else "/openapi.json",
    )

    app.state.settings = settings
    app.state.limiter = limiter

    @app.exception_handler(RateLimitExceeded)
    async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
        return JSONResponse(
            status_code=429,
            content={"detail": "Rate limit exceeded. Please try again later."},
        )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=_allowed_origins(),
        allow_credentials=_cors_allow_credentials(),
        allow_methods=_cors_methods(),
        allow_headers=_cors_headers(),
    )

    @app.get("/")
    @limiter.limit("60/minute")
    async def root(request: Request) -> dict[str, str]:
        return {"status": "running", "service": "ipu-ai-security-filter-backend"}

    @app.get("/health")
    @limiter.limit("60/minute")
    async def health(request: Request) -> dict[str, str]:
        # ``mode`` is informational and not used by any orchestrator; drop
        # it in public mode so unauthenticated probes learn less.
        if public:
            return {"status": "ok"}
        return {"status": "healthy", "mode": "manual-preview"}

    app.include_router(api_router)
    return app


app = create_app()
