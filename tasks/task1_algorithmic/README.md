# Task 1 — Alarm event grouping (~1 hour)

## The data

`data/alarms.csv` contains ~50,000 raw alarms with columns:

| column | type | notes |
|--------|------|-------|
| `alarm_id` | string | unique id for the raw alarm |
| `timestamp` | ISO-8601 | when the alarm fired (see note on timezones below) |
| `camera_id` | string | the camera that raised it |
| `alarm_type` | string | e.g. `motion`, `person`, `vehicle`, `tamper` |

> The file is generated; it is intentionally messy. Read it before you trust it.

## What to build

1. **Event grouping.** Alarms on the **same camera** within `T` seconds of one another
   form a single event. Make `T` a parameter (default `60`). For each event output:
   event id, camera id, start time, end time, alarm count, and the set of alarm types
   involved.

   **Windowing definition — use a session / chaining window.** A new alarm joins the
   current event if it is within `T` seconds of the **previous alarm** (not of the
   event's first alarm). An event therefore keeps extending as long as alarms keep
   arriving less than `T` seconds apart, and closes once a gap larger than `T` appears.
   Example with `T = 60`:

   ```
   12:00:00  -> starts event A
   12:00:50  -> 50s after previous -> joins A
   12:01:30  -> 40s after previous -> joins A   (A now spans 12:00:00–12:01:30)
   12:03:00  -> 90s after previous -> gap > 60s -> starts event B
   ```

2. **Anomaly flagging.** Identify cameras whose **event rate over the last 7 days** is
   anomalous relative to the **prior 30 days**. Define "anomalous" yourself and justify it.

   **Hint on the time windows:** compute "last 7 days" and "prior 30 days" relative to
   the **maximum timestamp present in the dataset** (in UTC), not relative to today's
   real-world date. The data spans exactly 37 days, so anchoring to the max timestamp
   and comparing in UTC avoids an off-by-a-day from calendar or local-time bucketing.

3. **Write-up (in this README or a separate file).** Cover time/space complexity, the
   data structures you chose and rejected, and how you treated the edge cases below.

## Processing model

You may read the whole file into memory and sort it — that is a perfectly good solution
for 50k rows, and we won't penalise it. You do **not** need to build a streaming
emulator (generators/queues/line-by-line). When we say we're interested in your
"windowing logic", we mean *how you reason about the windowing and ordering*, not that
you must simulate a live stream. If you'd like to comment on how your approach would
change for an unbounded stream that doesn't fit in memory, do so briefly in the
write-up — but it's optional.

## Output format

Write the grouped events to a file (CSV or JSON Lines — your choice) with these fields:
`event_id, camera_id, start, end, alarm_count, alarm_types`. Represent **`alarm_types`
as a sorted, comma-separated list**, e.g. `"motion,person"`. Timestamps in ISO-8601 UTC.

## Edge cases we baked in (handle them)

- Rows are **not** guaranteed to be in timestamp order.
- **Duplicate timestamps** on the same camera occur.
- Long **idle gaps** exist for some cameras.
- There is at least one **timezone wrinkle** — don't assume everything is UTC-naive.

## What we're assessing

Windowing logic, sorting-vs-hashing trade-offs, edge-case handling, and the clarity of
your complexity reasoning. Correctness and clear thinking beat cleverness.

## Deliverable

Runnable code (state how to run it) plus your write-up. No need for a UI or a database.
