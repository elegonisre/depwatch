"""Reminder logic: flag dependencies that have been outdated for too long."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import List

from depwatch.history import load_history


@dataclass
class RemindEntry:
    project: str
    package: str
    current_version: str
    latest_version: str
    outdated_since: datetime
    days_outdated: int


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def find_long_outdated(
    history_path: str,
    project: str,
    min_days: int = 7,
) -> List[RemindEntry]:
    """Return packages that have been continuously outdated for at least *min_days*."""
    records = load_history(history_path)
    project_records = [r for r in records if r.get("project") == project]
    if not project_records:
        return []

    # Build per-package first-seen-outdated timestamp
    first_outdated: dict[str, dict] = {}
    for rec in project_records:
        ts_str = rec.get("timestamp", "")
        try:
            ts = datetime.fromisoformat(ts_str)
        except (ValueError, TypeError):
            continue
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)
        for dep in rec.get("dependencies", []):
            name = dep.get("name", "")
            if not dep.get("is_outdated"):
                # Reset — it was up-to-date at this point
                first_outdated.pop(name, None)
            else:
                if name not in first_outdated:
                    first_outdated[name] = {"ts": ts, "dep": dep}

    now = _utcnow()
    results: List[RemindEntry] = []
    for name, info in first_outdated.items():
        delta = now - info["ts"]
        days = delta.days
        if days >= min_days:
            dep = info["dep"]
            results.append(
                RemindEntry(
                    project=project,
                    package=name,
                    current_version=dep.get("current_version", ""),
                    latest_version=dep.get("latest_version", ""),
                    outdated_since=info["ts"],
                    days_outdated=days,
                )
            )
    results.sort(key=lambda e: e.days_outdated, reverse=True)
    return results


def format_remind_report(entries: List[RemindEntry]) -> str:
    if not entries:
        return "No long-outdated dependencies found."
    lines = ["Long-outdated dependencies:", ""]
    for e in entries:
        lines.append(
            f"  [{e.project}] {e.package}: {e.current_version} -> {e.latest_version} "
            f"(outdated for {e.days_outdated}d since {e.outdated_since.date()})"
        )
    return "\n".join(lines)
