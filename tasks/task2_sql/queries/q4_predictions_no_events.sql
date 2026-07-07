WITH bounds AS (
    SELECT
        max(alarm_ts) AS max_alarm_ts,
        max(alarm_ts) - INTERVAL '14 days' AS window_start
    FROM alarms
),
cameras_with_predictions AS (
    SELECT DISTINCT
        a.camera_id
    FROM model_predictions mp
    JOIN alarms a
        ON a.alarm_id = mp.alarm_id
),
cameras_with_confirmed_events AS (
    SELECT DISTINCT
        a.camera_id
    FROM bounds b
    JOIN alarms a
        ON a.alarm_ts >= b.window_start
       AND a.alarm_ts <= b.max_alarm_ts
    JOIN dispositions d
        ON d.alarm_id = a.alarm_id
    WHERE d.outcome = 'true_alarm'
)
SELECT
    c.camera_id,
    c.camera_name,
    s.site_id,
    s.site_name,
    s.customer_id,
    s.customer_name
FROM cameras_with_predictions p
JOIN cameras c
    ON c.camera_id = p.camera_id
JOIN sites s
    ON s.site_id = c.site_id
LEFT JOIN cameras_with_confirmed_events confirmed
    ON confirmed.camera_id = c.camera_id
WHERE confirmed.camera_id IS NULL
ORDER BY
    c.camera_id;