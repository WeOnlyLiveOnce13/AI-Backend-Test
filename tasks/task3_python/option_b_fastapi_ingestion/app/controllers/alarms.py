from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query

from ..dependencies import get_alarm_service
from ..schemas import AlarmEvent, BulkIngestResponse
from ..services.alarm_service import AlarmService

router = APIRouter()


@router.post("/alarms", response_model=AlarmEvent)
async def ingest_alarm(
    event: AlarmEvent,
    service: Annotated[AlarmService, Depends(get_alarm_service)],
) -> AlarmEvent:
    return await service.ingest_alarm(event)


@router.post("/alarms/bulk", response_model=BulkIngestResponse)
async def ingest_bulk(
    events: list[AlarmEvent],
    service: Annotated[AlarmService, Depends(get_alarm_service)],
) -> BulkIngestResponse:
    if not events:
        raise HTTPException(status_code=400, detail="bulk request cannot be empty")

    ingested_count = await service.ingest_bulk(events)
    return BulkIngestResponse(ingested_count=ingested_count)


@router.get("/cameras/{camera_id}/recent", response_model=list[AlarmEvent])
async def recent_for_camera(
    camera_id: str,
    service: Annotated[AlarmService, Depends(get_alarm_service)],
    limit: Annotated[int, Query(ge=1, le=1000)] = 20,
) -> list[AlarmEvent]:
    return await service.get_recent_events(camera_id, limit)
