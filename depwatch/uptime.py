"""Uptime tracking: how long each project has maintained a fully up-to-date state."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Dict, List, Optional

from depwatch.history import load_history


@dataclass
class UptimeEntry:
    project: str
    total_runs: int
    clean_runs: int          # runs where all deps were up-to-date
    uptime_pct: float        # clean_runs / total_runs * 100
    current_streak: int      # consecutive clean runs (most recent first)
    longest_streak: int
    last_clean: Optional[datetime]


def _is_clean(statuses: list) -> bool:
    """Return True if every dependency in the snapshot is up-to-date."""
    return all(s.get("is_latest", True) for s in statuses)


def compute_uptime(history_path: str, project: str) -> Optional[UptimeEntry]:
    """Compute uptime statistics for *project* from the history file."""
    records = [
        r for r in load_history(history_path)
        if r.get("project") == project
    ]
    if not records:
        return None

    # Sort oldest-first so streaks accumulate naturally
    records.sort(key=lambda r: r.get("timestamp", ""))

    total_runs = len(records)
    clean_runs = 0
    longest_streak = 0
    current_run = 0
    last_clean: Optional[datetime] = None

    for rec in records:
        if _is_clean(rec.get("statuses", [])):
            clean_runs += 1
            current_run += 1
            longest_streak = max(longest_streak, current_run)
            ts = rec.get("timestamp")
            if ts:
                last_clean = datetime.fromisoformat(ts).replace(tzinfo=timezone.utc)
        else:
            current_run = 0

    uptime_pct = (clean_runs / total_runs * 100) if total_runs else 0.0
    return UptimeEntry(
        project=project,
        total_runs=total_runs,
        clean_runs=clean_runs,
        uptime_pct=round(uptime_pct, 1),
        current_streak=current_run,
        longest_streak=longest_streak,
        last_clean=last_clean,
    )


def compute_all_uptime(history_path: str) -> List[UptimeEntry]:
    """Compute uptime for every project found in the history file."""
    records = load_history(history_path)
    projects = {r.get("project") for r in records if r.get("project")}
    results = [compute_uptime(history_path, p) for p in sorted(projects)]
    return [r for r in results if r is not None]


def format_uptime_report(entries: List[UptimeEntry]) -> str:
    if not entries:
        return "No uptime data available."
    lines = [f"{'Project':<30} {'Runs':>5} {'Clean':>6} {'Uptime%':>8} {'Streak':>7} {'Best':>5}"]
    lines.append("-" * 65)
    for e in entries:
        lines.append(
            f"{e.project:<30} {e.total_runs:>5} {e.clean_runs:>6} "
            f"{e.uptime_pct:>7.1f}% {e.current_streak:>7} {e.longest_streak:>5}"
        )
    return "\n".join(lines)
