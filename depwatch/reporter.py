"""Generate summary reports from dependency check results."""
from __future__ import annotations

import json
from datetime import datetime
from typing import List

from depwatch.checker import DependencyStatus


def generate_report(
    project_name: str,
    statuses: List[DependencyStatus],
    fmt: str = "text",
) -> str:
    """Return a formatted report string for the given statuses.

    Args:
        project_name: Human-readable name of the scanned project.
        statuses: List of DependencyStatus results.
        fmt: Output format – ``"text"`` or ``"json"``.

    Returns:
        Formatted report as a string.
    """
    if fmt == "json":
        return _json_report(project_name, statuses)
    return _text_report(project_name, statuses)


def _text_report(project_name: str, statuses: List[DependencyStatus]) -> str:
    lines: List[str] = [
        f"depwatch report — {project_name}",
        f"Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}",
        "-" * 44,
    ]
    outdated = [s for s in statuses if s.is_outdated]
    up_to_date = [s for s in statuses if not s.is_outdated]

    if outdated:
        lines.append(f"Outdated ({len(outdated)}):")
        for s in outdated:
            lines.append(f"  {s.package:<24} {s.current_version} → {s.latest_version}")
    else:
        lines.append("All dependencies are up to date.")

    if up_to_date:
        lines.append(f"Up to date ({len(up_to_date)}):")
        for s in up_to_date:
            lines.append(f"  {s.package:<24} {s.current_version}")

    lines.append("-" * 44)
    lines.append(f"Total: {len(statuses)}  Outdated: {len(outdated)}")
    return "\n".join(lines)


def _json_report(project_name: str, statuses: List[DependencyStatus]) -> str:
    payload = {
        "project": project_name,
        "generated": datetime.utcnow().isoformat(timespec="seconds"),
        "total": len(statuses),
        "outdated_count": sum(1 for s in statuses if s.is_outdated),
        "dependencies": [
            {
                "package": s.package,
                "current_version": s.current_version,
                "latest_version": s.latest_version,
                "is_outdated": s.is_outdated,
            }
            for s in statuses
        ],
    }
    return json.dumps(payload, indent=2)
