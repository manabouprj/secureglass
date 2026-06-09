"""
SecureGlass API — main FastAPI application.
Run: uvicorn src.api.main:app --reload
"""
from __future__ import annotations
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from ..config import get_settings
from ..db.models import init_db
from .routers import auth as auth_router
from .routers import alerts as alerts_router

logging.basicConfig(level=logging.INFO)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    logging.getLogger("startup").info("DB initialised; connectors: %s",
                                       get_settings().connector_status())
    yield


def create_app() -> FastAPI:
    s = get_settings()
    app = FastAPI(title=s.app_name, version="2.0", lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[o.strip() for o in s.cors_origins.split(",")],
        allow_methods=["*"], allow_headers=["*"], allow_credentials=True,
    )
    app.include_router(auth_router.router)
    app.include_router(alerts_router.router)

    @app.get("/")
    async def root():
        return {"service": s.app_name, "version": "2.0", "docs": "/docs"}

    return app


app = create_app()
