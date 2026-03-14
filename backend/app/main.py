from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router


def create_app() -> FastAPI:
    app = FastAPI(
        title="IPU AI Security Filter Backend",
        description="Manual mode security replacement workbench API",
        version="0.1.0",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/")
    async def root() -> dict[str, str]:
        return {"status": "running", "service": "ipu-ai-security-filter-backend"}

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "healthy", "mode": "manual-preview-placeholder"}

    app.include_router(api_router)
    return app


app = create_app()
