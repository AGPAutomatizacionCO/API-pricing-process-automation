from contextlib import asynccontextmanager
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.auth_routes import router as auth_router
from app.api.routes.db_routes import router as db_router
from app.api.routes.health_routes import router as health_router

from app.core.audit_logger import ensure_log_files
from app.core.config import get_settings


settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    ensure_log_files()
    yield


app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    lifespan=lifespan,
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_frontend_origins(),
    allow_credentials=True,
    allow_methods=[
        "GET",
        "POST",
        "PUT",
        "PATCH",
        "DELETE",
        "OPTIONS",
    ],
    allow_headers=[
        "Authorization",
        "Content-Type",
        "X-Requested-With",
    ],
)


@app.middleware("http")
async def request_tracking_middleware(
    request: Request,
    call_next,
):
    request_id = str(uuid4())

    response = await call_next(request)

    response.headers["X-Request-ID"] = request_id

    response.headers["Cache-Control"] = (
        "no-store, no-cache, must-revalidate"
    )

    response.headers["Pragma"] = "no-cache"

    response.headers["Expires"] = "0"

    response.headers["X-Content-Type-Options"] = "nosniff"

    response.headers["Referrer-Policy"] = "same-origin"

    return response


app.include_router(health_router)
app.include_router(db_router)
app.include_router(auth_router)


@app.get("/")
def root():
    return {
        "status": "ok",
        "application": settings.app_name,
        "environment": settings.app_env,
        "docs": "/docs",
    }

