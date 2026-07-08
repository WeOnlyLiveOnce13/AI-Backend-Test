from __future__ import annotations

import argparse
import csv
import time
from bisect import bisect_left
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path

DEFAULT_CSV = Path("data/alarms.csv")


@dataclass(frozen=True)
class Alarm:
    alarm_id: str
    camera_id: str
    timestamp: datetime


def parse_timestamp(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def load_rows(csv_path: Path, limit: int | None) -> list[dict[str, str]]:
    with csv_path.open() as f:
        rows = list(csv.DictReader(f))
    return rows[:limit] if limit else rows


def parse_alarms(rows: list[dict[str, str]]) -> list[Alarm]:
    return [
        Alarm(
            alarm_id=row["alarm_id"],
            camera_id=row["camera_id"],
            timestamp=parse_timestamp(row["timestamp"]),
        )
        for row in rows
    ]


def compute_recent_counts(alarms: list[Alarm], window_s: float) -> dict[str, int]:
    timestamps_by_camera: dict[str, list[datetime]] = defaultdict(list)

    for alarm in alarms:
        timestamps_by_camera[alarm.camera_id].append(alarm.timestamp)

    for timestamps in timestamps_by_camera.values():
        timestamps.sort()

    window = timedelta(seconds=window_s)
    results: dict[str, int] = {}

    for alarm in alarms:
        timestamps = timestamps_by_camera[alarm.camera_id]
        left = bisect_left(timestamps, alarm.timestamp - window)
        right = bisect_left(timestamps, alarm.timestamp)
        results[alarm.alarm_id] = right - left

    return results


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--window", type=float, default=60.0)
    ap.add_argument("--csv", type=Path, default=DEFAULT_CSV)
    args = ap.parse_args()

    rows = load_rows(args.csv, args.limit)

    start = time.perf_counter()
    alarms = parse_alarms(rows)
    results = compute_recent_counts(alarms, args.window)
    elapsed_ms = (time.perf_counter() - start) * 1000

    checksum = sum(results.values())
    print(f"rows processed : {len(rows)}")
    print(f"CHECKSUM       : {checksum}")
    print(f"elapsed        : {elapsed_ms:.1f} ms")


if __name__ == "__main__":
    main()