#!/usr/bin/env python3
"""Task 4 — code to optimize.

This script computes a simple per-alarm feature over the Task 1 dataset:

    recent_count(alarm) = how many alarms on the SAME camera fired *strictly earlier*
                          in time, within the preceding WINDOW seconds.

The implementation below is **correct but slow**. Your job (see README.md) is to make it
faster for large inputs without changing its output. It reads the alarms CSV from
Task 1.

It prints three things you should preserve:
  * rows processed
  * a CHECKSUM (sum of all recent_count values) — your optimized version must match it
  * elapsed milliseconds

Usage:
    python slow_code.py [--limit N] [--window 60] [--csv PATH]

`--limit` caps how many rows are processed (the naive version is too slow on the full
file). Part of the exercise is making the full ~50k-row file run quickly.
"""

from __future__ import annotations

import argparse
import csv
import time
from datetime import datetime
from pathlib import Path

DEFAULT_CSV = (
    Path(__file__).resolve().parents[1]
    / "task1_algorithmic" / "data" / "alarms.csv"
)


def load_rows(csv_path: Path, limit: int | None) -> list[dict]:
    with csv_path.open() as f:
        rows = list(csv.DictReader(f))
    return rows[:limit] if limit else rows


def compute_recent_counts(rows: list[dict], window_s: float) -> dict[str, int]:
    results: dict[str, int] = {}
    for i in range(len(rows)):
        row = rows[i]
        cam = row["camera_id"]
        # NOTE: the timestamp is parsed again on every comparison below.
        t_i = datetime.fromisoformat(row["timestamp"].replace("Z", "+00:00"))
        count = 0
        for j in range(len(rows)):                       # full scan for every row
            other = rows[j]
            if other["camera_id"] == cam:
                t_j = datetime.fromisoformat(other["timestamp"].replace("Z", "+00:00"))
                delta = (t_i - t_j).total_seconds()
                if 0 < delta <= window_s:
                    count += 1
        results[row["alarm_id"]] = count
    return results


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--limit", type=int, default=4000,
                    help="cap rows processed (naive version is slow on the full file)")
    ap.add_argument("--window", type=float, default=60.0)
    ap.add_argument("--csv", type=Path, default=DEFAULT_CSV)
    args = ap.parse_args()

    rows = load_rows(args.csv, args.limit)

    start = time.perf_counter()
    results = compute_recent_counts(rows, args.window)
    elapsed_ms = (time.perf_counter() - start) * 1000

    checksum = sum(results.values())
    print(f"rows processed : {len(rows)}")
    print(f"CHECKSUM       : {checksum}")
    print(f"elapsed        : {elapsed_ms:.1f} ms")


if __name__ == "__main__":
    main()
