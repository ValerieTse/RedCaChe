from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.db import init_db
from app.routers import crawler, export_obsidian, import_mock, posts, remove_check, review


def create_app() -> FastAPI:
    settings = get_settings()

    @asynccontextmanager
    async def lifespan(_: FastAPI):
        init_db()
        yield

    api = FastAPI(title=settings.app_name, lifespan=lifespan)
    api.add_middleware(
        CORSMiddleware,
        allow_origins=list(settings.cors_origins),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @api.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok", "app": settings.app_name}

    api.include_router(posts.router)
    api.include_router(import_mock.router)
    api.include_router(review.router)
    api.include_router(export_obsidian.router)
    api.include_router(crawler.router)
    api.include_router(remove_check.router)
    return api


app = create_app()
