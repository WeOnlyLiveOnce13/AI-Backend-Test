from fastapi.testclient import TestClient

from tasks.task3_python.option_b_fastapi_ingestion.app.dependencies import (
    get_alarm_service,
)
from tasks.task3_python.option_b_fastapi_ingestion.app.main import create_app


class FakeAlarmService:
    def __init__(self) -> None:
        self.events = {}

    async def ingest_alarm(self, event):
        self.events[event.alarm_id] = event
        return event

    async def ingest_bulk(self, events):
        for event in events:
            self.events[event.alarm_id] = event
        return len(events)

    async def get_recent_events(self, camera_id, limit):
        events = [
            event for event in self.events.values() if event.camera_id == camera_id
        ]
        newest = sorted(
            events,
            key=lambda event: (event.timestamp, event.alarm_id),
            reverse=True,
        )[:limit]
        return list(reversed(newest))


def make_client():
    app = create_app(use_lifespan=False)
    service = FakeAlarmService()
    app.dependency_overrides[get_alarm_service] = lambda: service
    return TestClient(app)


def test_health():
    client = make_client()

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_ingest_alarm():
    client = make_client()

    payload = {
        "alarm_id": "ALM-1",
        "camera_id": "CAM-1",
        "timestamp": "2026-06-20T12:00:00Z",
        "alarm_type": "person",
        "metadata": {"confidence": 0.91},
    }

    response = client.post("/alarms", json=payload)

    assert response.status_code == 200
    assert response.json()["alarm_id"] == "ALM-1"


def test_validation_rejects_naive_timestamp():
    client = make_client()

    payload = {
        "alarm_id": "ALM-1",
        "camera_id": "CAM-1",
        "timestamp": "2026-06-20T12:00:00",
        "alarm_type": "person",
    }

    response = client.post("/alarms", json=payload)

    assert response.status_code == 422


def test_bulk_out_of_order_events_return_chronologically():
    client = make_client()

    payload = [
        {
            "alarm_id": "ALM-3",
            "camera_id": "CAM-1",
            "timestamp": "2026-06-20T12:02:00Z",
            "alarm_type": "vehicle",
        },
        {
            "alarm_id": "ALM-1",
            "camera_id": "CAM-1",
            "timestamp": "2026-06-20T12:00:00Z",
            "alarm_type": "person",
        },
        {
            "alarm_id": "ALM-2",
            "camera_id": "CAM-1",
            "timestamp": "2026-06-20T12:01:00Z",
            "alarm_type": "motion",
        },
    ]

    bulk_response = client.post("/alarms/bulk", json=payload)
    recent_response = client.get("/cameras/CAM-1/recent?limit=3")

    assert bulk_response.status_code == 200
    assert bulk_response.json() == {"ingested_count": 3}
    assert recent_response.status_code == 200
    assert [event["alarm_id"] for event in recent_response.json()] == [
        "ALM-1",
        "ALM-2",
        "ALM-3",
    ]


def test_bulk_rejects_empty_list():
    client = make_client()

    response = client.post("/alarms/bulk", json=[])

    assert response.status_code == 400
