from __future__ import annotations

import argparse
import csv
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path

from utils import (
    format_utc_timestamp,
    parse_utc_timestamp,
    write_csv,
)

DEFAULT_INPUT = Path("data/alarms.csv")
DEFAULT_EVENTS_OUTPUT = Path("tasks/task1_algorithmic/output/events.csv")
DEFAULT_ANOMALIES_OUTPUT = Path("tasks/task1_algorithmic/output/anomalous_cameras.csv")


@dataclass(frozen=True)
class Alarm:
    alarm_id: str
    timestamp: datetime
    camera_id: str
    alarm_type: str


@dataclass
class EventBuilder:
    event_id: str
    camera_id: str
    start: datetime
    end: datetime
    alarm_count: int = 0
    alarm_types: set[str] = field(default_factory=set)

    def add_alarm(self, alarm: Alarm) -> None:
        self.end = alarm.timestamp
        self.alarm_count += 1
        self.alarm_types.add(alarm.alarm_type)


@dataclass(frozen=True)
class CameraAnomaly:
    camera_id: str
    prior_30d_events: int
    recent_7d_events: int
    prior_daily_rate: float
    recent_daily_rate: float
    rate_ratio: float | None
    reason: str


def read_alarms(path: Path) -> list[Alarm]:
    with path.open(newline="") as f:
        reader = csv.DictReader(f)
        return [
            Alarm(
                alarm_id=row["alarm_id"],
                timestamp=parse_utc_timestamp(row["timestamp"]),
                camera_id=row["camera_id"],
                alarm_type=row["alarm_type"],
            )
            for row in reader
        ]


def finalize_event(event: EventBuilder) -> dict[str, str | int]:
    return {
        "event_id": event.event_id,
        "camera_id": event.camera_id,
        "start": format_utc_timestamp(event.start),
        "end": format_utc_timestamp(event.end),
        "alarm_count": event.alarm_count,
        "alarm_types": ",".join(sorted(event.alarm_types)),
    }


def group_events(
    alarms: list[Alarm],
    threshold_seconds: int,
) -> list[dict[str, str | int]]:
    sorted_alarms = sorted(
        alarms,
        key=lambda alarm: (alarm.camera_id, alarm.timestamp, alarm.alarm_id),
    )

    events: list[dict[str, str | int]] = []
    current: EventBuilder | None = None
    previous_alarm: Alarm | None = None
    threshold = timedelta(seconds=threshold_seconds)
    next_event_id = 1

    for alarm in sorted_alarms:
        starts_new_event = (
            current is None
            or previous_alarm is None
            or alarm.camera_id != previous_alarm.camera_id
            or alarm.timestamp - previous_alarm.timestamp > threshold
        )

        if starts_new_event:
            if current is not None:
                events.append(finalize_event(current))

            current = EventBuilder(
                event_id=f"EVT-{next_event_id:06d}",
                camera_id=alarm.camera_id,
                start=alarm.timestamp,
                end=alarm.timestamp,
            )
            next_event_id += 1

        current.add_alarm(alarm)
        previous_alarm = alarm

    if current is not None:
        events.append(finalize_event(current))

    return events


def find_anomalous_cameras(
    events: list[dict[str, str | int]],
    max_timestamp: datetime,
) -> list[CameraAnomaly]:
    recent_start = max_timestamp - timedelta(days=7)
    prior_start = recent_start - timedelta(days=30)

    counts: dict[str, dict[str, int]] = defaultdict(lambda: {"prior": 0, "recent": 0})

    for event in events:
        camera_id = str(event["camera_id"])
        event_start = parse_utc_timestamp(str(event["start"]))

        if prior_start <= event_start < recent_start:
            counts[camera_id]["prior"] += 1
        elif recent_start <= event_start <= max_timestamp:
            counts[camera_id]["recent"] += 1

    anomalies: list[CameraAnomaly] = []

    for camera_id, window_counts in sorted(counts.items()):
        prior_count = window_counts["prior"]
        recent_count = window_counts["recent"]

        prior_rate = prior_count / 30
        recent_rate = recent_count / 7

        if prior_count == 0:
            if recent_count >= 5:
                anomalies.append(
                    CameraAnomaly(
                        camera_id=camera_id,
                        prior_30d_events=prior_count,
                        recent_7d_events=recent_count,
                        prior_daily_rate=prior_rate,
                        recent_daily_rate=recent_rate,
                        rate_ratio=None,
                        reason="new_spike",
                    )
                )
            continue

        rate_ratio = recent_rate / prior_rate if prior_rate > 0 else None
        enough_volume = prior_count >= 5 or recent_count >= 5

        if enough_volume and rate_ratio is not None and rate_ratio >= 2:
            reason = "recent_rate_at_least_2x_prior"
        elif enough_volume and rate_ratio is not None and rate_ratio <= 0.5:
            reason = "recent_rate_at_most_half_prior"
        else:
            continue

        anomalies.append(
            CameraAnomaly(
                camera_id=camera_id,
                prior_30d_events=prior_count,
                recent_7d_events=recent_count,
                prior_daily_rate=prior_rate,
                recent_daily_rate=recent_rate,
                rate_ratio=rate_ratio,
                reason=reason,
            )
        )

    return anomalies


def anomalies_to_rows(anomalies: list[CameraAnomaly]) -> list[dict[str, str | int]]:
    rows: list[dict[str, str | int]] = []

    for anomaly in anomalies:
        rows.append(
            {
                "camera_id": anomaly.camera_id,
                "prior_30d_events": anomaly.prior_30d_events,
                "recent_7d_events": anomaly.recent_7d_events,
                "prior_daily_rate": f"{anomaly.prior_daily_rate:.4f}",
                "recent_daily_rate": f"{anomaly.recent_daily_rate:.4f}",
                "rate_ratio": (
                    "" if anomaly.rate_ratio is None else f"{anomaly.rate_ratio:.4f}"
                ),
                "reason": anomaly.reason,
            }
        )

    return rows


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--threshold-seconds", type=int, default=60)
    parser.add_argument("--events-output", type=Path, default=DEFAULT_EVENTS_OUTPUT)
    parser.add_argument(
        "--anomalies-output",
        type=Path,
        default=DEFAULT_ANOMALIES_OUTPUT,
    )
    args = parser.parse_args()

    alarms = read_alarms(args.input)
    events = group_events(alarms, args.threshold_seconds)

    max_timestamp = max(alarm.timestamp for alarm in alarms)
    anomalies = find_anomalous_cameras(events, max_timestamp)

    write_csv(
        args.events_output,
        ["event_id", "camera_id", "start", "end", "alarm_count", "alarm_types"],
        events,
    )
    write_csv(
        args.anomalies_output,
        [
            "camera_id",
            "prior_30d_events",
            "recent_7d_events",
            "prior_daily_rate",
            "recent_daily_rate",
            "rate_ratio",
            "reason",
        ],
        anomalies_to_rows(anomalies),
    )

    print(f"alarms read       : {len(alarms)}")
    print(f"events written    : {len(events)}")
    print(f"anomalies written : {len(anomalies)}")
    print(f"max timestamp UTC : {format_utc_timestamp(max_timestamp)}")
    print(f"events output     : {args.events_output}")
    print(f"anomalies output  : {args.anomalies_output}")


if __name__ == "__main__":
    main()