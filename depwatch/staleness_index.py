"""Compute a per-project staleness index — a weighted score (0-100)
that combines the ratio of outdated deps, average version gap, and
how long the project has gone without a clean run."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List

from depwatch.checker import DependencyStatus


@dataclass
class StalenessIndex:
    project: str
    total: int
    outdated: int
    avg_major_gap: float
    avg_minor_gap: float
    score: float          # 0 (fresh) – 100 (very stale)
    label: str


def _version_gap(current: str, latest: str) -> tuple[int, int]:
    """Return (major_gap, minor_gap) between two version strings."""
    def _parts(v: str) -> list[int]:
        parts = []
        for seg in v.split("."):
            try:
                parts.append(int(seg))
            except ValueError:
                parts.append(0)
        while len(parts) < 3:
            parts.append(0)
        return parts

    c = _parts(current)
    l = _parts(latest)
    major_gap = max(0, l[0] - c[0])
    minor_gap = max(0, l[1] - c[1]) if major_gap == 0 else 0
    return major_gap, minor_gap


def _staleness_label(score: float) -> str:
    if score >= 75:
        return "critical"
    if score >= 50:
        return "high"
    if score >= 25:
        return "moderate"
    return "low"


def compute_staleness_index(
    project: str,
    statuses: List[DependencyStatus],
) -> StalenessIndex:
    """Compute the staleness index for a single project."""
    total = len(statuses)
    if total == 0:
        return StalenessIndex(project, 0, 0, 0.0, 0.0, 0.0, "low")

    outdated = [s for s in statuses if s.is_outdated]
    n_out = len(outdated)

    ratio_score = (n_out / total) * 40  # up to 40 pts

    major_gaps, minor_gaps = [], []
    for s in outdated:
        mg, mng = _version_gap(s.current_version, s.latest_version)
        major_gaps.append(mg)
        minor_gaps.append(mng)

    avg_major = sum(major_gaps) / n_out if n_out else 0.0
    avg_minor = sum(minor_gaps) / n_out if n_out else 0.0

    gap_score = min(avg_major * 10, 40) + min(avg_minor * 2, 20)  # up to 60 pts

    raw = ratio_score + gap_score
    score = round(min(raw, 100.0), 2)
    return StalenessIndex(
        project=project,
        total=total,
        outdated=n_out,
        avg_major_gap=round(avg_major, 2),
        avg_minor_gap=round(avg_minor, 2),
        score=score,
        label=_staleness_label(score),
    )


def format_staleness_report(entries: List[StalenessIndex]) -> str:
    if not entries:
        return "No data available."
    lines = ["Staleness Index Report", "=" * 40]
    for e in sorted(entries, key=lambda x: x.score, reverse=True):
        lines.append(
            f"{e.project}: {e.score:.1f}/100 [{e.label.upper()}] "
            f"({e.outdated}/{e.total} outdated, "
            f"avg major gap: {e.avg_major_gap}, avg minor gap: {e.avg_minor_gap})"
        )
    return "\n".join(lines)
