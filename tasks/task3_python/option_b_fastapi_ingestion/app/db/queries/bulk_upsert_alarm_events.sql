INSERT INTO alarm_events (
    alarm_id,
    camera_id,
    event_ts,
    alarm_type,
    metadata
)
VALUES ($1, $2, $3, $4, $5::jsonb)
ON CONFLICT (alarm_id) DO UPDATE SET
    camera_id = EXCLUDED.camera_id,
    event_ts = EXCLUDED.event_ts,
    alarm_type = EXCLUDED.alarm_type,
    metadata = EXCLUDED.metadata,
    ingested_at = now();
