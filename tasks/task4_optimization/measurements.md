# Task 4 Measurements

All timings were collected locally on macOS using the provided Task 1 alarms CSV copied to `data/alarms.csv`.

## Results

| Script | Rows | Checksum | Elapsed |
| --- | ---: | ---: | ---: |
| `slow_code.py` | 1,000 | 11 | 27.3 ms |
| `optimized.py` | 1,000 | 11 | 0.6 ms |
| `slow_code.py` | 4,000 | 351 | 446.3 ms |
| `optimized.py` | 4,000 | 351 | 2.9 ms |
| `slow_code.py` | 50,513 | 54,214 | 77,839.8 ms |
| `optimized.py` | 50,513 | 54,214 | 48.0 ms |

On the full file, the optimized version is approximately `1,622x` faster while producing the same checksum.

## What Changed

The original implementation is correct but slow because it scans the full row list for every alarm and reparses timestamps inside the nested loop.

The optimized implementation:

- parses timestamps once,
- groups timestamps by camera,
- sorts timestamps per camera,
- uses binary search to count timestamps in `[current_time - window, current_time)`,
- excludes duplicate timestamps correctly because the upper bound uses `bisect_left(current_time)`.

The interval is inclusive at the lower bound and exclusive at the upper bound, matching the requirement:

```text
0 < current_time - previous_time <= window
```


## Complexity

Original implementation:

```text
O(n²)
```

It compares each alarm against every other alarm.

Optimized implementation:

```text
O(n log n)
```

The cost is dominated by sorting timestamps per camera. Counting is done with binary search.

## Edge Cases Preserved

- Out-of-order input rows are handled by sorting per camera.
- Duplicate timestamps do not count as "strictly earlier".
- Only alarms from the same camera are considered.
- The checksum matches the slow implementation at 1,000 rows, 4,000 rows, and the full file.

## With More Time

I would add a small benchmark harness that runs each implementation multiple times and reports median/p95 runtime, plus property-style tests that compare the optimized implementation against the slow implementation on generated edge-case datasets.

## My Solution

See `optimized.py` for the optimized implementation and `measurements.md` for timings.

The optimized script can be run with:

```bash
uv run python tasks/task4_optimization/optimized.py --csv data/alarms.csv
```

The provided CSV is kept locally under `data/alarms.csv` and ignored by Git.

On my local run, the full-file checksum matched the slow implementation:

```text
CHECKSUM: 54214
```

The optimized version processed the full file in `48.0 ms` versus `77,839.8 ms` for the slow version.

## Verification

```bash
uv run python tasks/task4_optimization/optimized.py --limit 4000 --csv data/alarms.csv
uv run ruff check tasks/task4_optimization
```