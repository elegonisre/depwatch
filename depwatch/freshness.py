"""Freshness scoring: how recently each dependency was last up-to-date."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import List, Optional

from depwatch.history import load_history


@dataclass
class FreshnessEntry:
    project: str
    package: str
    last_up_to_date: Optional[datetime]   # None if never seen up-to-date
    days_stale: Optional[int]              # None if never seen up-to-date
    freshness_score: float                 # 0.0 (very stale) – 1.0 (fresh)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _score(days: Optional[int], decay: int = 30) -> float:
    """Exponential decay: score = e^(-days/decay), clamped to [0, 1]."""
    if days is None:
        return 0.0
    import math
    return round(math.exp(-days / decay), 4)


def compute_freshness(
    history_path: str,
    project: Optional[str] = None,
    decay_days: int = 30,
) -> List[FreshnessEntry]:
    """Return a freshness entry per (project, package) pair."""
    records = load_history(history_path)
    if project:
        records = [r for r in records if r.get("project") == project]

    # Track the most recent timestamp where each package was up-to-date
    last_ok: dict[tuple[str, str], datetime] = {}

    for rec in records:
        proj = rec.get("project", "")
        ts_raw = rec.get("timestamp")
        try:
            ts = datetime.fromisoformat(ts_raw).replace(tzinfo=timezone.utc)
        except (TypeError, ValueError):
            continue
        for dep in rec.get("statuses", []):
            if not dep.get("is_outdated", True):
                key = (proj, dep["package"])
                if key not in last_ok or ts > last_ok[key]:
                    last_ok[key] = ts

    # Collect all (project, package) pairs ever seen
    all_pairs: set[tuple[str, str]] = set()
    for rec in records:
        proj = rec.get("project", "")
        for dep in rec.get("statuses", []):
            all_pairs.add((proj, dep["package"]))

    now = _utcnow()
    entries: List[FreshnessEntry] = []
    for proj, pkg in sorted(all_pairs):
        last = last_ok.get((proj, pkg))
        days = int((now - last).total_seconds() / 86400) if last else None
        entries.append(
            FreshnessEntry(
                project=proj,
                package=pkg,
                last_up_to_date=last,
                days_stale=days,
                freshness_score=_score(days, decay_days),
            )
        )
    return entries


def format_freshness_report(entries: List[FreshnessEntry]) -> str:
    if not entries:
        return "No freshness data available."
    lines = [f"{'Project':<20} {'Package':<25} {'Days stale':>10} {'Score':>7}"]
    lines.append("-" * 66)
    for e in entries:
        days = str(e.days_stale) if e.days_stale is not None else "never ok"
        lines.append(f"{e.project:<20} {e.package:<25} {days:>10} {e.freshness_score:>7.4f}")
    return "\n".join(lines)
