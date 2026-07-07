WITH date_bounds AS (
    SELECT
        min(a.alarm_ts)::date AS start_date,
        max(a.alarm_ts)::date AS end_date
    FROM alarms a
),
calendar AS (
    SELECT generate_series(
        (SELECT start_date FROM date_bounds),
        (SELECT end_date FROM date_bounds),
        INTERVAL '1 day'
    )::date AS alarm_date
),
camera_calendar AS (
    SELECT
        c.camera_id,
        c.camera_name,
        cal.alarm_date
    FROM cameras c
    CROSS JOIN calendar cal
),
daily_dispositions AS (
    SELECT
        a.camera_id,
        a.alarm_ts::date AS alarm_date,
        count(*) AS disposition_count,
        count(*) FILTER (WHERE d.outcome = 'false_alarm') AS false_alarm_count
    FROM alarms a
    JOIN dispositions d
        ON d.alarm_id = a.alarm_id
    GROUP BY
        a.camera_id,
        a.alarm_ts::date
),
daily_filled AS (
    SELECT
        cc.camera_id,
        cc.camera_name,
        cc.alarm_date,
        COALESCE(dd.disposition_count, 0) AS disposition_count,
        COALESCE(dd.false_alarm_count, 0) AS false_alarm_count
    FROM camera_calendar cc
    LEFT JOIN daily_dispositions dd
        ON dd.camera_id = cc.camera_id
       AND dd.alarm_date = cc.alarm_date
),
rolling_rates AS (
    SELECT
        camera_id,
        camera_name,
        alarm_date,
        sum(false_alarm_count) OVER (
            PARTITION BY camera_id
            ORDER BY alarm_date
            ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
        ) AS rolling_false_alarms_7d,
        sum(disposition_count) OVER (
            PARTITION BY camera_id
            ORDER BY alarm_date
            ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
        ) AS rolling_dispositions_7d
    FROM daily_filled
),
rates_with_previous_week AS (
    SELECT
        camera_id,
        camera_name,
        alarm_date,
        rolling_false_alarms_7d,
        rolling_dispositions_7d,
        CASE
            WHEN rolling_dispositions_7d = 0 THEN NULL
            ELSE rolling_false_alarms_7d::numeric / rolling_dispositions_7d
        END AS false_alarm_rate_7d,
        lag(
            CASE
                WHEN rolling_dispositions_7d = 0 THEN NULL
                ELSE rolling_false_alarms_7d::numeric / rolling_dispositions_7d
            END,
            7
        ) OVER (
            PARTITION BY camera_id
            ORDER BY alarm_date
        ) AS previous_week_false_alarm_rate_7d
    FROM rolling_rates
)
SELECT
    camera_id,
    camera_name,
    alarm_date,
    rolling_false_alarms_7d,
    rolling_dispositions_7d,
    round(false_alarm_rate_7d, 4) AS false_alarm_rate_7d,
    round(previous_week_false_alarm_rate_7d, 4) AS previous_week_false_alarm_rate_7d,
    CASE
        WHEN previous_week_false_alarm_rate_7d IS NULL
          OR previous_week_false_alarm_rate_7d = 0
          OR false_alarm_rate_7d IS NULL
        THEN NULL
        ELSE round(
            (
                false_alarm_rate_7d - previous_week_false_alarm_rate_7d
            )
            / previous_week_false_alarm_rate_7d,
            4
        )
    END AS week_over_week_change,
    CASE
        WHEN previous_week_false_alarm_rate_7d IS NULL
          OR previous_week_false_alarm_rate_7d = 0
          OR false_alarm_rate_7d IS NULL
        THEN false
        ELSE abs(
            (
                false_alarm_rate_7d - previous_week_false_alarm_rate_7d
            )
            / previous_week_false_alarm_rate_7d
        ) > 0.50
    END AS is_week_over_week_change_gt_50pct
FROM rates_with_previous_week
WHERE rolling_dispositions_7d > 0
ORDER BY
    camera_id,
    alarm_date;