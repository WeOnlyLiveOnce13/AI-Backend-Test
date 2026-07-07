## Q6 Optimisation

The original query asks for, per camera, the number of alarms and false alarms in the 14 days up to `2026-06-21`, ordered by busiest cameras first.

The provided slow query used two correlated subqueries:

```sql
(SELECT count(*) FROM alarms a WHERE a.camera_id = c.camera_id ...)
```

and:

```sql
(SELECT count(*) FROM dispositions d JOIN alarms a2 ... WHERE a2.camera_id = c.camera_id ...)
```

Because those subqueries were correlated with each row from `cameras`, PostgreSQL ran them once per camera. In the provided plan, 
both subplans had `loops=300`, so the `alarms` table was scanned repeatedly. The plan also showed many rows removed by filter on each scan.

The slow query also used:

```sql
a.alarm_ts::date >= DATE '2026-06-07'
```

Casting the timestamp column makes it harder for PostgreSQL to use a timestamp index efficiently. I replaced it with a half-open timestamp range:

```sql
a.alarm_ts >= TIMESTAMPTZ '2026-06-07 00:00:00+00'
AND a.alarm_ts < TIMESTAMPTZ '2026-06-22 00:00:00+00'
```

The optimized query in `queries/q6_optimised.sql` first filters recent alarms once, joins dispositions once, then aggregates by `camera_id`:

```sql
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
```

Measured on my local Docker Postgres setup:

| Query | Execution time |
| --- | ---: |
| Provided slow query | `4124.602 ms` |
| Optimized query | `11.470 ms` |

That is roughly a `359x` speedup.

The optimized plan scans `alarms` once and keeps `13,011` recent rows from `55,000`, then joins to `dispositions` and aggregates by camera. The final sort is only over `300` camera rows.

For a production schema, I would also add a timestamp-oriented index for this access pattern:

```sql
CREATE INDEX idx_alarms_alarm_ts_camera_id
ON alarms (alarm_ts, camera_id);
```

The provided schema intentionally has minimal indexes, so the main improvement here is query shape: replacing repeated correlated scans with one filtered aggregate.