import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import asyncpg

from ..schemas import AlarmEvent

SQL_DIR = Path(__file__).resolve().parents[1] / "db"
QUERY_DIR = SQL_DIR / "queries"


def load_sql(path: Path) -> str:
    return path.read_text(encoding="utf-8")


CREATE_SCHEMA_SQL = load_sql(SQL_DIR / "schema.sql")
UPSERT_ALARM_EVENT_SQL = load_sql(QUERY_DIR / "upsert_alarm_event.sql")
BULK_UPSERT_ALARM_EVENTS_SQL = load_sql(QUERY_DIR / "bulk_upsert_alarm_events.sql")
SELECT_RECENT_ALARM_EVENTS_SQL = load_sql(
    QUERY_DIR / "select_recent_alarm_events_by_camera.sql"
)


def metadata_to_json(metadata: dict[str, Any] | None) -> str | None:
    if metadata is None:
        return None
    return json.dumps(metadata)


def metadata_from_db(value: Any) -> dict[str, Any] | None:
    if value is None:
        return None
    if isinstance(value, str):
        return json.loads(value)
    return value


def row_to_event(row: asyncpg.Record) -> AlarmEvent:
    event_ts: datetime = row["event_ts"]
    if event_ts.tzinfo is None:
        event_ts = event_ts.replace(tzinfo=UTC)

    return AlarmEvent(
        alarm_id=row["alarm_id"],
        camera_id=row["camera_id"],
        timestamp=event_ts.astimezone(UTC),
        alarm_type=row["alarm_type"],
        metadata=metadata_from_db(row["metadata"]),
    )


class AlarmRepository:
    def __init__(self, pool: asyncpg.Pool) -> None:
        self._pool = pool

    async def init_schema(self) -> None:
        async with self._pool.acquire() as conn:
            await conn.execute(CREATE_SCHEMA_SQL)

    async def upsert_event(self, event: AlarmEvent) -> AlarmEvent:
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                UPSERT_ALARM_EVENT_SQL,
                event.alarm_id,
                event.camera_id,
                event.timestamp,
                event.alarm_type,
                metadata_to_json(event.metadata),
            )
        return row_to_event(row)

    async def upsert_events(self, events: list[AlarmEvent]) -> None:
        if not events:
            return

        rows = [
            (
                event.alarm_id,
                event.camera_id,
                event.timestamp,
                event.alarm_type,
                metadata_to_json(event.metadata),
            )
            for event in events
        ]

        async with self._pool.acquire() as conn:
            async with conn.transaction():
                await conn.executemany(BULK_UPSERT_ALARM_EVENTS_SQL, rows)

    async def get_recent_events(self, camera_id: str, limit: int) -> list[AlarmEvent]:
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(SELECT_RECENT_ALARM_EVENTS_SQL, camera_id, limit)

        events = [row_to_event(row) for row in rows]
        return list(reversed(events))
