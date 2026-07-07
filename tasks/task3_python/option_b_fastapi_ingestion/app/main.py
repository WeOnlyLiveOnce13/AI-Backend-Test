"""Minimal FastAPI scaffold for Task 3, Option B.

This is a STARTER. It boots and exposes a health check and stub endpoints so you can
focus on design. Wire up Postgres + Redis, validation, and tests yourself.
"""

from __future__ import annotations

from datetime import datetime

from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="DeepAlert Alarm Ingestion (candidate scaffold)")


class AlarmEvent(BaseModel):
    alarm_id: str
    camera_id: str
    timestamp: datetime
    alarm_type: str
    metadata: dict | None = None


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}


@app.post("/alarms")
async def ingest_alarm(event: AlarmEvent) -> dict:
    # TODO: persist to Postgres, update Redis cache for event.camera_id
    raise NotImplementedError


@app.post("/alarms/bulk")
async def ingest_bulk(events: list[AlarmEvent]) -> dict:
    # TODO: efficient bulk insert
    raise NotImplementedError


@app.get("/cameras/{camera_id}/recent")
async def recent_for_camera(camera_id: str, limit: int = 20) -> list[AlarmEvent]:
    # TODO: serve from Redis, fall back to Postgres
    raise NotImplementedError
