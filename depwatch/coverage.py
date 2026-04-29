"""Dependency coverage: tracks what fraction of dependencies are being monitored."""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Sequence

from depwatch.checker import DependencyStatus


@dataclass
class CoverageReport:
    project: str
    total: int
    monitored: int
    unmonitored: List[str]
    coverage_pct: float
    grade: str


def _grade(pct: float) -> str:
    if pct >= 95:
        return "A"
    if pct >= 80:
        return "B"
    if pct >= 60:
        return "C"
    if pct >= 40:
        return "D"
    return "F"


def compute_coverage(
    project: str,
    all_deps: Sequence[str],
    statuses: Sequence[DependencyStatus],
) -> CoverageReport:
    """Compute how many of *all_deps* appear in the monitored *statuses*."""
    monitored_names = {s.package for s in statuses}
    total = len(all_deps)
    monitored = sum(1 for d in all_deps if d in monitored_names)
    unmonitored = [d for d in all_deps if d not in monitored_names]
    pct = (monitored / total * 100) if total > 0 else 100.0
    return CoverageReport(
        project=project,
        total=total,
        monitored=monitored,
        unmonitored=unmonitored,
        coverage_pct=round(pct, 1),
        grade=_grade(pct),
    )


def format_coverage_report(reports: Sequence[CoverageReport]) -> str:
    if not reports:
        return "No coverage data available."
    lines: List[str] = []
    for r in reports:
        lines.append(f"[{r.project}] Coverage: {r.coverage_pct}% ({r.monitored}/{r.total}) Grade: {r.grade}")
        if r.unmonitored:
            lines.append("  Unmonitored: " + ", ".join(r.unmonitored))
    return "\n".join(lines)
