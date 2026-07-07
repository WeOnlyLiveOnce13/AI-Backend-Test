import json
from datetime import UTC
from typing import Any

from redis.asyncio import Redis

from ..schemas import AlarmEvent


def cache_key(camera_id: str) -> str:
    return f"recent:{camera_id}"


def event_score(event: AlarmEvent) -> float:
    return event.timestamp.astimezone(UTC).timestamp()


def event_to_json(event: AlarmEvent) -> str:
    data = event.model_dump(mode="json")
    return json.dumps(data, separators=(",", ":"), sort_keys=True)


def event_from_json(value: str | bytes) -> AlarmEvent:
    if isinstance(value, bytes):
        value = value.decode("utf-8")
    return AlarmEvent.model_validate(json.loads(value))


class RecentEventCache:
    def __init__(self, redis: Redis, max_size: int) -> None:
        self._redis = redis
        self._max_size = max_size

    async def add_event(self, event: AlarmEvent) -> None:
        key = cache_key(event.camera_id)
        await self._redis.zadd(key, {event_to_json(event): event_score(event)})
        await self._redis.zremrangebyrank(key, 0, -(self._max_size + 1))

    async def add_many(self, events: list[AlarmEvent]) -> None:
        if not events:
            return

        pipe = self._redis.pipeline(transaction=False)

        for event in events:
            key = cache_key(event.camera_id)
            pipe.zadd(key, {event_to_json(event): event_score(event)})
            pipe.zremrangebyrank(key, 0, -(self._max_size + 1))

        await pipe.execute()

    async def get_recent(self, camera_id: str, limit: int) -> list[AlarmEvent]:
        values: list[Any] = await self._redis.zrevrange(
            cache_key(camera_id),
            0,
            limit - 1,
        )
        events = [event_from_json(value) for value in values]
        return list(reversed(events))
