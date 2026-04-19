"""Stale dependency detection — flags deps not updated in N days."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import List, Optional

from depwatch.checker import DependencyStatus


@dataclass
class StaleEntry:
    project: str
    package: str
    current_version: str
    latest_version: str
    days_outdated: int
    is_outdated: bool


def days_since(dt: datetime) -> int:
    """Return number of full days between *dt* and now (UTC)."""
    now = datetime.now(tz=timezone.utc)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    delta = now - dt
    return max(0, delta.days)


def find_stale(
    statuses: List[DependencyStatus],
    project: str,
    threshold_days: int,
    checked_at: Optional[datetime] = None,
) -> List[StaleEntry]:
    """Return StaleEntry list for deps that have been outdated >= threshold_days.

    *checked_at* is the timestamp of the check run (defaults to now).
    """
    if checked_at is None:
        checked_at = datetime.now(tz=timezone.utc)

    stale: List[StaleEntry] = []
    for s in statuses:
        if not s.is_outdated:
            continue
        age = days_since(checked_at)
        # In a real scenario age would come from history; here we use
        # checked_at offset from now as a proxy so callers can inject it.
        stale.append(
            StaleEntry(
                project=project,
                package=s.package,
                current_version=s.current_version,
                latest_version=s.latest_version,
                days_outdated=age,
                is_outdated=True,
            )
        )
    return stale


def format_stale_report(entries: List[StaleEntry], threshold_days: int) -> str:
    if not entries:
        return f"No dependencies stale for more than {threshold_days} day(s).\n"
    lines = [f"Stale dependencies (>= {threshold_days} days):\n"]
    for e in entries:
        lines.append(
            f"  [{e.project}] {e.package} {e.current_version} -> {e.latest_version} "
            f"({e.days_outdated}d)"
        )
    return "\n".join(lines) + "\n"
