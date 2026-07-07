# Task 4 — Code optimization (~30 minutes, hard cap)

A short, focused task: make slow code fast without changing what it computes. This is
about performance instinct and measurement, not cleverness.

## The code

`slow_code.py` computes a per-alarm feature over the **Task 1 alarms CSV**:

> `recent_count(alarm)` = how many alarms on the **same camera** fired **strictly earlier
> in time**, within the preceding `WINDOW` seconds (default 60).

It is **correct but slow**. Run it:

```bash
python slow_code.py --limit 4000
```

It prints `rows processed`, a `CHECKSUM` (sum of all `recent_count` values), and
`elapsed` milliseconds. The naive version is too slow to run on the full ~50k-row file,
which is why `--limit` exists.

## Your task

1. Produce an optimized version (e.g. `optimized.py`) that returns the **identical**
   result — same `CHECKSUM` for any given `--limit` and `--window`.
2. Make it fast enough to process the **full file** (drop `--limit`) quickly.
3. Report the numbers: baseline ms vs optimized ms at the same `--limit`, and the time to
   process the full file. A short paragraph on *what* you changed and *why* it helps.

## Rules

- **30-minute hard cap.** This task is meant to be quick — don't gold-plate it.
- Keep the output identical (matching `CHECKSUM`). An optimization that changes results is
  not an optimization.
- Pure-Python standard library is enough to get a large win. You may use third-party
  libraries if you justify the dependency, but it isn't necessary.
- Preserve correctness on the data's quirks (out-of-order rows, duplicate timestamps).

## What we're assessing

That you can spot algorithmic and per-iteration inefficiencies, fix them, and **measure**
the improvement honestly. Be ready to explain the complexity before and after, and where
the time was actually going.

## Deliverable

Your optimized script + a few lines reporting before/after timings and the change you
made. Keep the original `slow_code.py` so the comparison is reproducible.
