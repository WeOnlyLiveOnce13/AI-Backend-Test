CREATE TABLE IF NOT EXISTS alarm_events (
    alarm_id TEXT PRIMARY KEY,
    camera_id TEXT NOT NULL,
    event_ts TIMESTAMPTZ NOT NULL,
    alarm_type TEXT NOT NULL,
    metadata JSONB,
    ingested_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_alarm_events_camera_ts
ON alarm_events (camera_id, event_ts DESC);
