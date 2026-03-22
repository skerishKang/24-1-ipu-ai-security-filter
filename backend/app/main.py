import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

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


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.manual_preview_service = ManualPreviewService()
    yield


def create_app() -> FastAPI:
    app = FastAPI(
        title="IPU AI Firewall Backend",
        description="Manual mode security replacement workbench API",
        version="0.1.0",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=_allowed_origins(),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/")
    async def root() -> dict[str, str]:
        return {"status": "running", "service": "ipu-ai-firewall-backend"}

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "healthy", "mode": "manual-preview"}

    app.include_router(api_router)
    return app


app = create_app()
