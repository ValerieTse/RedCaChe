from __future__ import annotations

import asyncio
import logging
from contextlib import asynccontextmanager, suppress

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.db import init_db
from app.routers import (
    config as config_router,
    crawler,
    export_obsidian,
    import_mock,
    posts,
    remove_check,
    review,
)
from app.services.daily_fetch import daily_fetch_loop


def create_app() -> FastAPI:
    settings = get_settings()

    @asynccontextmanager
    async def lifespan(_: FastAPI):
        logging.basicConfig(level=logging.INFO)
        init_db()
        fetch_task = (
            asyncio.create_task(daily_fetch_loop(settings))
            if settings.daily_fetch_enabled
            else None
        )
        yield
        if fetch_task is not None:
            fetch_task.cancel()
            with suppress(asyncio.CancelledError):
                await fetch_task

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

    api.include_router(config_router.router)
    api.include_router(posts.router)
    api.include_router(import_mock.router)
    api.include_router(review.router)
    api.include_router(export_obsidian.router)
    api.include_router(crawler.router)
    api.include_router(remove_check.router)
    return api


app = create_app()
