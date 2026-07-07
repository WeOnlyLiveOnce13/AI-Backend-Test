from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


class AlarmEvent(BaseModel):
    alarm_id: str = Field(min_length=1)
    camera_id: str = Field(min_length=1)
    timestamp: datetime
    alarm_type: str = Field(min_length=1)
    metadata: dict[str, Any] | None = None

    model_config = ConfigDict(extra="forbid")

    @field_validator("timestamp")
    @classmethod
    def require_timezone(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("timestamp must include a timezone")
        return value.astimezone(UTC)


class BulkIngestResponse(BaseModel):
    ingested_count: int
