"""Compute the age of each dependency's current installed version vs latest."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional, List

import requests

from depwatch.checker import DependencyStatus


@dataclass
class DependencyAge:
    project: str
    package: str
    installed_version: str
    latest_version: str
    installed_release_date: Optional[datetime]
    latest_release_date: Optional[datetime]
    days_behind: Optional[int]
    is_outdated: bool


def _fetch_release_date(package: str, version: str) -> Optional[datetime]:
    """Return the upload date for *version* of *package* from PyPI."""
    try:
        resp = requests.get(
            f"https://pypi.org/pypi/{package}/{version}/json", timeout=10
        )
        resp.raise_for_status()
        data = resp.json()
        releases = data.get("urls", [])
        if not releases:
            return None
        upload_time = releases[0].get("upload_time_iso_8601") or releases[0].get("upload_time")
        if upload_time is None:
            return None
        upload_time = upload_time.rstrip("Z")
        dt = datetime.fromisoformat(upload_time)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except Exception:
        return None


def compute_dependency_ages(
    project: str, statuses: List[DependencyStatus]
) -> List[DependencyAge]:
    """Return DependencyAge records for each status in *statuses*."""
    results: List[DependencyAge] = []
    for s in statuses:
        installed_date = _fetch_release_date(s.package, s.installed_version)
        if s.is_outdated:
            latest_date = _fetch_release_date(s.package, s.latest_version)
        else:
            latest_date = installed_date

        days_behind: Optional[int] = None
        if installed_date and latest_date and latest_date > installed_date:
            delta = latest_date - installed_date
            days_behind = delta.days
        elif installed_date and latest_date:
            days_behind = 0

        results.append(
            DependencyAge(
                project=project,
                package=s.package,
                installed_version=s.installed_version,
                latest_version=s.latest_version,
                installed_release_date=installed_date,
                latest_release_date=latest_date,
                days_behind=days_behind,
                is_outdated=s.is_outdated,
            )
        )
    return results


def format_age_table(entries: List[DependencyAge]) -> str:
    """Return a human-readable table of dependency ages."""
    if not entries:
        return "No dependency age data available."
    lines = [f"{'Package':<30} {'Installed':<12} {'Latest':<12} {'Days Behind':>12}"]
    lines.append("-" * 70)
    for e in sorted(entries, key=lambda x: (x.days_behind or 0), reverse=True):
        days = str(e.days_behind) if e.days_behind is not None else "unknown"
        lines.append(f"{e.package:<30} {e.installed_version:<12} {e.latest_version:<12} {days:>12}")
    return "\n".join(lines)
