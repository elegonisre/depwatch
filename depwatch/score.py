"""Health score calculation for projects based on dependency status."""
from dataclasses import dataclass
from typing import List
from depwatch.checker import DependencyStatus


@dataclass
class ProjectScore:
    project: str
    total: int
    outdated: int
    score: float  # 0.0 - 100.0
    grade: str


def _grade(score: float) -> str:
    if score >= 90:
        return "A"
    elif score >= 75:
        return "B"
    elif score >= 60:
        return "C"
    elif score >= 40:
        return "D"
    return "F"


def compute_score(project: str, statuses: List[DependencyStatus]) -> ProjectScore:
    total = len(statuses)
    if total == 0:
        return ProjectScore(project=project, total=0, outdated=0, score=100.0, grade="A")
    outdated = sum(1 for s in statuses if s.outdated)
    score = round((1 - outdated / total) * 100, 1)
    return ProjectScore(
        project=project,
        total=total,
        outdated=outdated,
        score=score,
        grade=_grade(score),
    )


def score_all(results: dict) -> List[ProjectScore]:
    """results: {project_name: [DependencyStatus, ...]}"""
    return [compute_score(proj, statuses) for proj, statuses in results.items()]


def format_scores(scores: List[ProjectScore]) -> str:
    lines = ["Dependency Health Scores", "=" * 40]
    for s in sorted(scores, key=lambda x: x.score):
        lines.append(
            f"  {s.project:<25} {s.grade}  {s.score:5.1f}%  "
            f"({s.outdated}/{s.total} outdated)"
        )
    return "\n".join(lines)
