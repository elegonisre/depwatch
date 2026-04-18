"""Export dependency check results to various formats (CSV, JSON)."""
from __future__ import annotations

import csv
import io
import json
from typing import List

from depwatch.checker import DependencyStatus


def to_csv(project: str, statuses: List[DependencyStatus]) -> str:
    """Serialize statuses to CSV string."""
    output = io.StringIO()
    writer = csv.DictWriter(
        output,
        fieldnames=["project", "package", "current_version", "latest_version", "outdated"],
    )
    writer.writeheader()
    for s in statuses:
        writer.writerow(
            {
                "project": project,
                "package": s.package,
                "current_version": s.current_version,
                "latest_version": s.latest_version,
                "outdated": s.outdated,
            }
        )
    return output.getvalue()


def to_json(project: str, statuses: List[DependencyStatus]) -> str:
    """Serialize statuses to JSON string."""
    records = [
        {
            "project": project,
            "package": s.package,
            "current_version": s.current_version,
            "latest_version": s.latest_version,
            "outdated": s.outdated,
        }
        for s in statuses
    ]
    return json.dumps(records, indent=2)


def export_results(project: str, statuses: List[DependencyStatus], fmt: str) -> str:
    """Export results in the requested format ('csv' or 'json')."""
    if fmt == "csv":
        return to_csv(project, statuses)
    if fmt == "json":
        return to_json(project, statuses)
    raise ValueError(f"Unsupported export format: {fmt!r}. Choose 'csv' or 'json'.")
