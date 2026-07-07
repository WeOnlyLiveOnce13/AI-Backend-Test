SELECT
    alarm_id,
    camera_id,
    event_ts,
    alarm_type,
    metadata
FROM alarm_events
WHERE camera_id = $1
ORDER BY event_ts DESC, alarm_id DESC
LIMIT $2;
