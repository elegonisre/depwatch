"""Project health scoring based on multiple depwatch signals."""
from __future__ import annotations

from dataclasses import dataclass
from typing import List

from depwatch.checker import DependencyStatus
from depwatch.score import compute_score
from depwatch.risk import assess_risk, RiskEntry
from depwatch.stale import find_stale


@dataclass
class HealthReport:
    project: str
    total: int
    outdated: int
    high_risk: int
    stale: int
    score: float          # 0-100
    grade: str
    summary: str


def _grade(score: float) -> str:
    if score >= 90:
        return "A"
    if score >= 75:
        return "B"
    if score >= 60:
        return "C"
    if score >= 40:
        return "D"
    return "F"


def compute_health(
    project: str,
    statuses: List[DependencyStatus],
    stale_days: int = 30,
) -> HealthReport:
    """Combine score, risk and stale signals into a single health report."""
    total = len(statuses)
    if total == 0:
        return HealthReport(
            project=project, total=0, outdated=0, high_risk=0,
            stale=0, score=100.0, grade="A", summary="No dependencies tracked."
        )

    ps = compute_score(project, statuses)
    base_score = ps.score

    risks: List[RiskEntry] = assess_risk(statuses)
    high_risk = sum(1 for r in risks if r.label in ("high", "critical"))

    stale_entries = find_stale(statuses, days=stale_days)
    stale_count = len(stale_entries)

    # Penalise: -2 per high-risk dep, -1 per stale dep (floor 0)
    penalty = high_risk * 2 + stale_count * 1
    final_score = max(0.0, min(100.0, base_score - penalty))

    outdated = sum(1 for s in statuses if s.current_version != s.latest_version)
    grade = _grade(final_score)
    summary = (
        f"{outdated}/{total} outdated, {high_risk} high-risk, "
        f"{stale_count} stale — grade {grade}"
    )

    return HealthReport(
        project=project,
        total=total,
        outdated=outdated,
        high_risk=high_risk,
        stale=stale_count,
        score=round(final_score, 1),
        grade=grade,
        summary=summary,
    )


def format_health_report(reports: List[HealthReport], fmt: str = "text") -> str:
    if fmt == "json":
        import json
        return json.dumps(
            [
                {
                    "project": r.project,
                    "total": r.total,
                    "outdated": r.outdated,
                    "high_risk": r.high_risk,
                    "stale": r.stale,
                    "score": r.score,
                    "grade": r.grade,
                    "summary": r.summary,
                }
                for r in reports
            ],
            indent=2,
        )
    lines = ["=== Dependency Health Report ==="]
    for r in reports:
        lines.append(f"\n[{r.project}]  Grade: {r.grade}  Score: {r.score}/100")
        lines.append(f"  {r.summary}")
    return "\n".join(lines)
