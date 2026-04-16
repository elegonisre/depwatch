"""Weekly/daily digest builder — aggregates history into a summary message."""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Dict, List, Tuple

from depwatch.history import load_history
from depwatch.trend import most_frequently_outdated, outdated_counts_over_time


def _since(days: int) -> str:
    return (datetime.utcnow() - timedelta(days=days)).isoformat()


def build_digest(history_path: str, days: int = 7) -> str:
    """Return a plain-text digest covering the last *days* days."""
    records = load_history(history_path)
    cutoff = _since(days)
    recent = [r for r in records if r.get("timestamp", "") >= cutoff]

    if not recent:
        return f"No data recorded in the last {days} day(s)."

    lines: List[str] = [
        f"=== depwatch digest (last {days} day(s)) ===",
        f"Runs included : {len(recent)}",
    ]

    counts = outdated_counts_over_time(recent)
    if counts:
        timestamps, values = zip(*counts)
        lines.append(f"Outdated counts: min={min(values)}  max={max(values)}  last={values[-1]}")

    top = most_frequently_outdated(recent, top_n=5)
    if top:
        lines.append("\nMost frequently outdated packages:")
        for pkg, freq in top:
            lines.append(f"  {pkg:<30} {freq} run(s)")

    projects: Dict[str, int] = {}
    for rec in recent:
        for dep in rec.get("dependencies", []):
            if dep.get("is_outdated"):
                proj = rec.get("project", "unknown")
                projects[proj] = projects.get(proj, 0) + 1

    if projects:
        lines.append("\nOutdated hits by project:")
        for proj, cnt in sorted(projects.items(), key=lambda x: -x[1]):
            lines.append(f"  {proj:<30} {cnt}")

    return "\n".join(lines)
