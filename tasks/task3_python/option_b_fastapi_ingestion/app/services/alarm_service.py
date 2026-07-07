from ..cache.recent_event_cache import RecentEventCache
from ..repositories.alarm_repository import AlarmRepository
from ..schemas import AlarmEvent


class AlarmService:
    def __init__(
        self,
        repository: AlarmRepository,
        cache: RecentEventCache,
        recent_cache_size: int,
    ) -> None:
        self._repository = repository
        self._cache = cache
        self._recent_cache_size = recent_cache_size

    async def ingest_alarm(self, event: AlarmEvent) -> AlarmEvent:
        saved = await self._repository.upsert_event(event)
        await self._cache.add_event(saved)
        return saved

    async def ingest_bulk(self, events: list[AlarmEvent]) -> int:
        await self._repository.upsert_events(events)
        await self._cache.add_many(events)
        return len(events)

    async def get_recent_events(self, camera_id: str, limit: int) -> list[AlarmEvent]:
        if limit <= self._recent_cache_size:
            cached_events = await self._cache.get_recent(camera_id, limit)
            if len(cached_events) >= limit:
                return cached_events

        events = await self._repository.get_recent_events(camera_id, limit)
        await self._cache.add_many(events)
        return events
