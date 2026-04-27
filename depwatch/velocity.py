"""Compute how quickly dependencies are becoming outdated over time."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Dict, List, Optional

from depwatch.history import load_history


@dataclass
class VelocityEntry:
    project: str
    outdated_per_day: float          # average new outdated deps per day
    total_outdated_delta: int        # net change over the window
    window_days: float               # actual time span analysed
    first_run: datetime
    last_run: datetime


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _parse_ts(ts: str) -> datetime:
    dt = datetime.fromisoformat(ts)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def compute_velocity(
    history_path: str,
    project: str,
    window_days: int = 30,
) -> Optional[VelocityEntry]:
    """Return a VelocityEntry for *project* using runs within *window_days*."""
    records = load_history(history_path)
    now = _utcnow()

    project_runs: List[Dict] = [
        r for r in records
        if r.get("project") == project
        and (now - _parse_ts(r["timestamp"])).days <= window_days
    ]

    if len(project_runs) < 2:
        return None

    project_runs.sort(key=lambda r: r["timestamp"])

    first = project_runs[0]
    last = project_runs[-1]

    first_ts = _parse_ts(first["timestamp"])
    last_ts = _parse_ts(last["timestamp"])
    span_days = max((last_ts - first_ts).total_seconds() / 86400, 1e-6)

    first_outdated = sum(
        1 for s in first.get("statuses", []) if not s.get("is_latest", True)
    )
    last_outdated = sum(
        1 for s in last.get("statuses", []) if not s.get("is_latest", True)
    )

    delta = last_outdated - first_outdated

    return VelocityEntry(
        project=project,
        outdated_per_day=delta / span_days,
        total_outdated_delta=delta,
        window_days=span_days,
        first_run=first_ts,
        last_run=last_ts,
    )


def format_velocity_report(entries: List[VelocityEntry]) -> str:
    if not entries:
        return "No velocity data available."

    lines = ["Dependency Velocity Report", "=" * 40]
    for e in entries:
        direction = "+" if e.total_outdated_delta >= 0 else ""
        lines.append(
            f"  {e.project}: {direction}{e.outdated_per_day:.3f} outdated/day "
            f"(delta {direction}{e.total_outdated_delta} over "
            f"{e.window_days:.1f} days)"
        )
    return "\n".join(lines)
