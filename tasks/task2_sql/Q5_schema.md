## Q5 Schema Design: Dispositions Storage

For production disposition storage, I would keep dispositions as an append-oriented table with timestamps stored as `TIMESTAMPTZ`. 
The stated pattern is "find dispositions for this camera over this time window", so I would denormalize `camera_id` and `alarm_ts` onto the disposition row instead of 
requiring every operational lookup to join through `alarms`.

```sql
CREATE TABLE dispositions (
    disposition_id   BIGINT GENERATED ALWAYS AS IDENTITY,
    alarm_id         BIGINT NOT NULL,
    camera_id        INTEGER NOT NULL,
    alarm_ts         TIMESTAMPTZ NOT NULL,
    outcome          TEXT NOT NULL CHECK (
        outcome IN ('false_alarm', 'true_alarm', 'ignored')
    ),
    operator_id      INTEGER NOT NULL,
    acknowledged_at  TIMESTAMPTZ NOT NULL,
    dispatched_at    TIMESTAMPTZ,
    created_at       TIMESTAMPTZ NOT NULL DEFAULT now(),

    PRIMARY KEY (disposition_id, alarm_ts),
    UNIQUE (alarm_id, alarm_ts)
) PARTITION BY RANGE (alarm_ts);
```

I would partition by month on `alarm_ts` and retain 24 monthly partitions for the two-year retention period. Monthly partitions are a practical balance as they make retention cheap through `DROP TABLE` on old partitions, while avoiding the planning overhead of very small daily partitions.

Example partition:

```sql
CREATE TABLE dispositions_2026_06
PARTITION OF dispositions
FOR VALUES FROM ('2026-06-01') TO ('2026-07-01');
```

The most important index for the stated lookup pattern is:

```sql
CREATE INDEX idx_dispositions_camera_alarm_ts
ON dispositions (camera_id, alarm_ts DESC);
```

That supports queries like:

```sql
WHERE camera_id = $1
  AND alarm_ts >= $2
  AND alarm_ts < $3
```

For operational dashboards that filter by outcome, I would add partial indexes only where query volume justifies them:

```sql
CREATE INDEX idx_dispositions_true_alarm_camera_ts
ON dispositions (camera_id, alarm_ts DESC)
WHERE outcome = 'true_alarm';

CREATE INDEX idx_dispositions_false_alarm_camera_ts
ON dispositions (camera_id, alarm_ts DESC)
WHERE outcome = 'false_alarm';
```

I would keep the foreign key from `alarm_id` to `alarms(alarm_id)` in a normal production system. At very high ingestion volumes, 
I might enforce that relationship asynchronously, but I would not start there because referential integrity is valuable for operator outcome data.

With more time, I would benchmark monthly versus weekly partitions with realistic query volumes, add automated future partition creation, and consider BRIN indexes for very large 
append-only timestamp scans.