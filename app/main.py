from fastapi import FastAPI

from app.api.v1.router import api_router
from app.core.config import get_settings
from app.core.exceptions import install_exception_handlers
from app.core.logging import configure_logging
from app.db.init_db import init_local_database


def create_app() -> FastAPI:
    configure_logging()
    settings = get_settings()
    app = FastAPI(title=settings.app_name, debug=settings.debug)
    install_exception_handlers(app)

    @app.on_event("startup")
    def startup() -> None:
        init_local_database()

    @app.get("/health", tags=["health"])
    def health() -> dict:
        return {"status": "ok", "environment": settings.environment}

    app.include_router(api_router)
    app.include_router(api_router, prefix=settings.api_v1_prefix)
    return app


app = create_app()
