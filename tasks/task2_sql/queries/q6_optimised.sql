-- Issues:
-- 1. It uses correlated subqueries.
-- 2. Those subqueries run once per camera.
-- 3. It casts alarm_ts::date, making timestamp indexes less useful.
-- 4. It scans alarms repeatedly.

-- Improvements over the slow query:
--   1. Scan the recent alarms once instead of running correlated subqueries per camera.
--   2. Use a half-open timestamp range instead of alarm_ts::date.
--   3. Aggregate with FILTER instead of separate subqueries.

WITH recent_alarm_counts AS (
    SELECT
        a.camera_id,
        count(*) AS recent_alarms,
        count(*) FILTER (WHERE d.outcome = 'false_alarm') AS recent_false_alarms
    FROM alarms a
    LEFT JOIN dispositions d
        ON d.alarm_id = a.alarm_id
    WHERE a.alarm_ts >= TIMESTAMPTZ '2026-06-07 00:00:00+00'
      AND a.alarm_ts < TIMESTAMPTZ '2026-06-22 00:00:00+00'
    GROUP BY
        a.camera_id
)
SELECT
    c.camera_id,
    c.camera_name,
    COALESCE(r.recent_alarms, 0) AS recent_alarms,
    COALESCE(r.recent_false_alarms, 0) AS recent_false_alarms
FROM cameras c
LEFT JOIN recent_alarm_counts r
    ON r.camera_id = c.camera_id
ORDER BY
    recent_false_alarms DESC,
    recent_alarms DESC,
    c.camera_id ASC;