"""Compute how long each dependency has been outdated based on history."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Dict, List, Optional

from depwatch.history import load_history


@dataclass
class OutdatedAge:
    project: str
    package: str
    first_seen_outdated: datetime
    days_outdated: int
    current_version: str
    latest_version: str


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def compute_outdated_ages(
    history_path: str, project: Optional[str] = None
) -> List[OutdatedAge]:
    """Return OutdatedAge entries for each package that is currently outdated."""
    records = load_history(history_path)
    if project:
        records = [r for r in records if r.get("project") == project]

    # Track first time each (project, package) was seen outdated
    first_seen: Dict[tuple, dict] = {}
    last_seen: Dict[tuple, dict] = {}

    for rec in records:
        proj = rec.get("project", "")
        for dep in rec.get("dependencies", []):
            if not dep.get("is_outdated"):
                continue
            key = (proj, dep["package"])
            if key not in first_seen:
                first_seen[key] = {"ts": rec["timestamp"], "dep": dep}
            last_seen[key] = {"ts": rec["timestamp"], "dep": dep}

    now = _utcnow()
    results: List[OutdatedAge] = []
    for key, info in first_seen.items():
        proj, pkg = key
        ts_str = info["ts"]
        try:
            first_dt = datetime.fromisoformat(ts_str)
        except ValueError:
            continue
        if first_dt.tzinfo is None:
            first_dt = first_dt.replace(tzinfo=timezone.utc)
        days = (now - first_dt).days
        dep = last_seen[key]["dep"]
        results.append(
            OutdatedAge(
                project=proj,
                package=pkg,
                first_seen_outdated=first_dt,
                days_outdated=days,
                current_version=dep.get("current_version", ""),
                latest_version=dep.get("latest_version", ""),
            )
        )

    results.sort(key=lambda e: e.days_outdated, reverse=True)
    return results


def format_age_report(entries: List[OutdatedAge]) -> str:
    if not entries:
        return "No outdated dependencies found in history."
    lines = ["Outdated Dependency Age Report", "=" * 40]
    for e in entries:
        lines.append(
            f"[{e.project}] {e.package}: {e.current_version} -> {e.latest_version} "
            f"(outdated for {e.days_outdated} day(s))"
        )
    return "\n".join(lines)
