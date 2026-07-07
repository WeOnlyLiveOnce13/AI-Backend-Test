from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from redis.asyncio import Redis

from .cache.recent_event_cache import RecentEventCache
from .config import get_settings
from .controllers.alarms import router as alarms_router
from .db.pool import create_pool
from .repositories.alarm_repository import AlarmRepository
from .services.alarm_service import AlarmService


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()

    pool = await create_pool(settings.database_url)
    redis = Redis.from_url(settings.redis_url, decode_responses=True)

    repository = AlarmRepository(pool)
    await repository.init_schema()

    cache = RecentEventCache(redis, settings.recent_cache_size)

    app.state.settings = settings
    app.state.pool = pool
    app.state.redis = redis
    app.state.alarm_repository = repository
    app.state.recent_event_cache = cache
    app.state.alarm_service = AlarmService(
        repository=repository,
        cache=cache,
        recent_cache_size=settings.recent_cache_size,
    )

    try:
        yield
    finally:
        await redis.aclose()
        await pool.close()


def create_app(use_lifespan: bool = True) -> FastAPI:
    app = FastAPI(
        title="DeepAlert Alarm Ingestion",
        lifespan=lifespan if use_lifespan else None,
    )

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    app.include_router(alarms_router)
    return app


app = create_app()
