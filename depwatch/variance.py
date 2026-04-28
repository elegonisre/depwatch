"""Variance analysis: measures how consistently a project keeps dependencies up to date over time."""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from depwatch.history import load_history


@dataclass
class VarianceEntry:
    project: str
    run_count: int
    mean_outdated: float
    variance: float
    std_dev: float
    min_outdated: int
    max_outdated: int
    stability_label: str


def _stability_label(std_dev: float) -> str:
    if std_dev < 1.0:
        return "stable"
    if std_dev < 3.0:
        return "moderate"
    return "volatile"


def _count_outdated(records: list) -> int:
    return sum(1 for r in records if r.get("installed_version") != r.get("latest_version"))


def compute_variance(history_file: str, project: str) -> Optional[VarianceEntry]:
    """Compute variance of outdated-dependency counts across all recorded runs for *project*."""
    history = load_history(history_file)
    runs = [entry for entry in history if entry.get("project") == project]
    if not runs:
        return None

    # Group records by run timestamp
    from collections import defaultdict
    by_run: dict = defaultdict(list)
    for record in runs:
        by_run[record.get("timestamp", "")].append(record)

    counts: List[int] = [_count_outdated(recs) for recs in by_run.values()]
    if not counts:
        return None

    n = len(counts)
    mean = sum(counts) / n
    variance = sum((c - mean) ** 2 for c in counts) / n
    std_dev = variance ** 0.5

    return VarianceEntry(
        project=project,
        run_count=n,
        mean_outdated=round(mean, 2),
        variance=round(variance, 2),
        std_dev=round(std_dev, 2),
        min_outdated=min(counts),
        max_outdated=max(counts),
        stability_label=_stability_label(std_dev),
    )


def compute_all_variance(history_file: str) -> List[VarianceEntry]:
    """Compute variance entries for every project present in the history file."""
    history = load_history(history_file)
    projects = {entry.get("project") for entry in history if entry.get("project")}
    results = []
    for project in sorted(projects):
        entry = compute_variance(history_file, project)
        if entry is not None:
            results.append(entry)
    return results


def format_variance_report(entries: List[VarianceEntry]) -> str:
    if not entries:
        return "No variance data available."
    lines = ["Dependency Update Variance Report", "=" * 40]
    for e in entries:
        lines.append(
            f"  {e.project}: runs={e.run_count}, mean={e.mean_outdated}, "
            f"std_dev={e.std_dev}, range=[{e.min_outdated},{e.max_outdated}], "
            f"stability={e.stability_label}"
        )
    return "\n".join(lines)
