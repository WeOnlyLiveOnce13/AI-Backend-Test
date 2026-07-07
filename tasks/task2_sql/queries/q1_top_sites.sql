WITH params AS (
    SELECT
        TIMESTAMPTZ '2026-06-01 00:00:00+00' AS start_ts,
        TIMESTAMPTZ '2026-06-22 00:00:00+00' AS end_ts,
        10::integer AS top_n
)


SELECT
    s.site_id,
    s.customer_id,
    s.customer_name,
    s.site_name,
    s.region,
    count(*) AS alarm_count


FROM params p
JOIN alarms a
    ON a.alarm_ts >= p.start_ts
   AND a.alarm_ts < p.end_ts
JOIN cameras c
    ON c.camera_id = a.camera_id
JOIN sites s
    ON s.site_id = c.site_id

GROUP BY
    s.site_id,
    s.customer_id,
    s.customer_name,
    s.site_name,
    s.region

ORDER BY
    alarm_count DESC,
    s.site_id ASC
LIMIT (SELECT top_n FROM params);