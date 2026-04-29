"""Cadence analysis: how regularly each project is checked."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import List, Optional

from depwatch.history import load_history


@dataclass
class CadenceEntry:
    project: str
    run_count: int
    first_seen: Optional[datetime]
    last_seen: Optional[datetime]
    avg_interval_hours: Optional[float]
    regularity_label: str


def _parse_ts(ts: str) -> datetime:
    return datetime.fromisoformat(ts).replace(tzinfo=timezone.utc)


def _regularity_label(avg_hours: Optional[float]) -> str:
    if avg_hours is None:
        return "unknown"
    if avg_hours <= 1:
        return "very frequent"
    if avg_hours <= 12:
        return "frequent"
    if avg_hours <= 48:
        return "regular"
    if avg_hours <= 168:
        return "infrequent"
    return "rare"


def compute_cadence(history_path: str) -> List[CadenceEntry]:
    records = load_history(history_path)
    by_project: dict[str, list[datetime]] = {}
    for rec in records:
        project = rec.get("project", "unknown")
        ts_str = rec.get("timestamp")
        if ts_str:
            by_project.setdefault(project, []).append(_parse_ts(ts_str))

    entries: List[CadenceEntry] = []
    for project, timestamps in sorted(by_project.items()):
        timestamps.sort()
        first = timestamps[0]
        last = timestamps[-1]
        run_count = len(timestamps)
        if run_count >= 2:
            gaps = [
                (timestamps[i + 1] - timestamps[i]).total_seconds() / 3600
                for i in range(len(timestamps) - 1)
            ]
            avg_interval: Optional[float] = sum(gaps) / len(gaps)
        else:
            avg_interval = None
        entries.append(
            CadenceEntry(
                project=project,
                run_count=run_count,
                first_seen=first,
                last_seen=last,
                avg_interval_hours=avg_interval,
                regularity_label=_regularity_label(avg_interval),
            )
        )
    return entries


def format_cadence_report(entries: List[CadenceEntry]) -> str:
    if not entries:
        return "No cadence data available."
    lines = ["Cadence Report", "=" * 40]
    for e in entries:
        avg = f"{e.avg_interval_hours:.1f}h" if e.avg_interval_hours is not None else "n/a"
        last = e.last_seen.strftime("%Y-%m-%d %H:%M") if e.last_seen else "n/a"
        lines.append(
            f"{e.project}: {e.run_count} runs | avg interval {avg} | "
            f"{e.regularity_label} | last {last}"
        )
    return "\n".join(lines)
