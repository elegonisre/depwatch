"""Summary module: produce a high-level health summary across all projects."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Dict

from depwatch.checker import DependencyStatus


@dataclass
class ProjectSummary:
    project: str
    total: int
    outdated: int
    up_to_date: int
    outdated_ratio: float  # 0.0 – 1.0
    grade: str


def _grade(ratio: float) -> str:
    """Return a letter grade based on the outdated ratio."""
    if ratio == 0.0:
        return "A"
    if ratio <= 0.1:
        return "B"
    if ratio <= 0.25:
        return "C"
    if ratio <= 0.5:
        return "D"
    return "F"


def summarise_project(project: str, statuses: List[DependencyStatus]) -> ProjectSummary:
    """Build a ProjectSummary for a single project."""
    total = len(statuses)
    outdated = sum(1 for s in statuses if s.is_outdated)
    up_to_date = total - outdated
    ratio = outdated / total if total else 0.0
    return ProjectSummary(
        project=project,
        total=total,
        outdated=outdated,
        up_to_date=up_to_date,
        outdated_ratio=ratio,
        grade=_grade(ratio),
    )


def summarise_all(
    results: Dict[str, List[DependencyStatus]]
) -> List[ProjectSummary]:
    """Return a ProjectSummary for every project, sorted by outdated_ratio desc."""
    summaries = [summarise_project(proj, stats) for proj, stats in results.items()]
    return sorted(summaries, key=lambda s: s.outdated_ratio, reverse=True)


def format_summary(summaries: List[ProjectSummary]) -> str:
    """Render summaries as a human-readable text table."""
    if not summaries:
        return "No projects to summarise."

    lines = [f"{'Project':<30} {'Total':>6} {'Outdated':>9} {'Up-to-date':>11} {'Ratio':>7} {'Grade':>6}"]
    lines.append("-" * 75)
    for s in summaries:
        lines.append(
            f"{s.project:<30} {s.total:>6} {s.outdated:>9} {s.up_to_date:>11}"
            f" {s.outdated_ratio:>6.0%} {s.grade:>6}"
        )
    total_deps = sum(s.total for s in summaries)
    total_out = sum(s.outdated for s in summaries)
    lines.append("-" * 75)
    overall = total_out / total_deps if total_deps else 0.0
    lines.append(f"{'TOTAL':<30} {total_deps:>6} {total_out:>9} {total_deps - total_out:>11} {overall:>6.0%}")
    return "\n".join(lines)
