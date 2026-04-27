"""Dependency maturity scoring — rates how 'mature' each dependency is
based on version number, release age, and how far behind the project is."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from depwatch.checker import DependencyStatus


@dataclass
class MaturityEntry:
    project: str
    package: str
    current_version: str
    latest_version: str
    major_version: int          # major of latest release
    is_outdated: bool
    versions_behind: int        # rough gap in major versions
    maturity_score: float       # 0.0 (immature/risky) – 1.0 (stable)
    label: str                  # "stable" | "maturing" | "young" | "legacy"


def _parse_major(version: str) -> int:
    """Return the major version component, or 0 on parse failure."""
    try:
        return int(version.split(".")[0])
    except (ValueError, IndexError, AttributeError):
        return 0


def _maturity_label(score: float) -> str:
    if score >= 0.75:
        return "stable"
    if score >= 0.50:
        return "maturing"
    if score >= 0.25:
        return "young"
    return "legacy"


def compute_maturity(
    statuses: List[DependencyStatus],
    project: str = "default",
) -> List[MaturityEntry]:
    """Compute a maturity entry for every dependency status."""
    entries: List[MaturityEntry] = []
    for s in statuses:
        latest_major = _parse_major(s.latest_version or "0")
        current_major = _parse_major(s.current_version or "0")
        gap = max(latest_major - current_major, 0)

        # Score: penalise being outdated and large version gaps.
        # Reward high major version numbers (indicates maturity of the project).
        base = min(latest_major / 10.0, 1.0) if latest_major > 0 else 0.0
        penalty = min(gap * 0.15, 0.6) if s.is_outdated else 0.0
        score = round(max(base - penalty, 0.0), 3)

        entries.append(
            MaturityEntry(
                project=project,
                package=s.package,
                current_version=s.current_version or "unknown",
                latest_version=s.latest_version or "unknown",
                major_version=latest_major,
                is_outdated=s.is_outdated,
                versions_behind=gap,
                maturity_score=score,
                label=_maturity_label(score),
            )
        )
    return entries


def format_maturity_report(entries: List[MaturityEntry]) -> str:
    """Return a human-readable maturity report."""
    if not entries:
        return "No dependency maturity data available."

    lines = ["Dependency Maturity Report", "=" * 40]
    for e in sorted(entries, key=lambda x: x.maturity_score):
        flag = "[OUTDATED]" if e.is_outdated else ""
        lines.append(
            f"  {e.package:<30} {e.current_version:<12} -> {e.latest_version:<12}"
            f"  score={e.maturity_score:.2f}  [{e.label}]  {flag}"
        )
    avg = sum(e.maturity_score for e in entries) / len(entries)
    lines.append("-" * 40)
    lines.append(f"Average maturity score: {avg:.2f}")
    return "\n".join(lines)
