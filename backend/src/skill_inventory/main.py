import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError
from starlette.middleware.trustedhost import TrustedHostMiddleware

from skill_inventory.db import check_database
from skill_inventory.routes.admin import router as admin_router
from skill_inventory.routes.public import router as public_router
from skill_inventory.services.skills import SkillNotFound, SlugConflict


def create_app(health_check=None) -> FastAPI:
    app = FastAPI(title="Skill Inventory", version="0.1.0")
    app.add_middleware(
        TrustedHostMiddleware, allowed_hosts=["localhost", "127.0.0.1"], www_redirect=False
    )

    @app.middleware("http")
    async def check_management_origin(request: Request, call_next):
        if request.url.path.startswith("/api/admin/") and request.method not in {
            "GET",
            "HEAD",
            "OPTIONS",
        }:
            origin = request.headers.get("origin")
            if origin is not None and origin not in {
                "http://localhost:8080",
                "http://127.0.0.1:8080",
                "http://localhost:5173",
                "http://127.0.0.1:5173",
            }:
                return JSONResponse({"detail": "Untrusted origin"}, status_code=403)
        return await call_next(request)

    app.include_router(admin_router)
    app.include_router(public_router)

    @app.exception_handler(SkillNotFound)
    async def not_found(request: Request, exc: SkillNotFound):
        return JSONResponse({"detail": "Skill not found"}, status_code=404)

    @app.exception_handler(SlugConflict)
    async def conflict(request: Request, exc: SlugConflict):
        return JSONResponse({"detail": "Slug already exists"}, status_code=409)

    @app.get("/healthz")
    def health():
        try:
            (health_check or check_database)()
        except SQLAlchemyError:
            return JSONResponse({"detail": "Database unavailable"}, status_code=503)
        return {"status": "ok"}

    @app.exception_handler(SQLAlchemyError)
    async def database_error(request: Request, exc: SQLAlchemyError):
        logging.getLogger(__name__).error("Database operation failed (%s)", type(exc).__name__)
        return JSONResponse({"detail": "Database unavailable"}, status_code=503)

    return app


app = create_app()
