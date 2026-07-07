WITH dispatch_durations AS (
    SELECT
        s.customer_id,
        s.customer_name,
        EXTRACT(EPOCH FROM (d.dispatched_at - d.acknowledged_at)) AS dispatch_seconds
    FROM dispositions d
    JOIN alarms a
        ON a.alarm_id = d.alarm_id
    JOIN cameras c
        ON c.camera_id = a.camera_id
    JOIN sites s
        ON s.site_id = c.site_id
    WHERE d.dispatched_at IS NOT NULL
)
SELECT
    customer_id,
    customer_name,
    count(*) AS dispatched_alarm_count,
    count(*) FILTER (WHERE dispatch_seconds >= 0) AS valid_dispatch_count,
    count(*) FILTER (WHERE dispatch_seconds < 0) AS invalid_negative_dispatch_count,
    round(
        (
            percentile_cont(0.50) WITHIN GROUP (
                ORDER BY dispatch_seconds
            ) FILTER (WHERE dispatch_seconds >= 0)
        )::numeric,
        2
    ) AS p50_dispatch_seconds,
    round(
        (
            percentile_cont(0.95) WITHIN GROUP (
                ORDER BY dispatch_seconds
            ) FILTER (WHERE dispatch_seconds >= 0)
        )::numeric,
        2
    ) AS p95_dispatch_seconds
FROM dispatch_durations
GROUP BY
    customer_id,
    customer_name
ORDER BY
    customer_id;