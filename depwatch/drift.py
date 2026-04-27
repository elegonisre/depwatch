"""Dependency drift: measure how far a project's deps have drifted from latest."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from depwatch.checker import DependencyStatus


@dataclass
class DriftEntry:
    project: str
    package: str
    current_version: str
    latest_version: str
    major_gap: int
    minor_gap: int
    patch_gap: int
    drift_score: float  # weighted composite


def _parse(version: str) -> tuple[int, int, int]:
    """Parse a version string into (major, minor, patch) ints, tolerating short versions."""
    parts = version.split(".")
    nums: list[int] = []
    for p in parts[:3]:
        try:
            nums.append(int(p.split("+")[0].split("a")[0].split("b")[0].split("rc")[0]))
        except ValueError:
            nums.append(0)
    while len(nums) < 3:
        nums.append(0)
    return nums[0], nums[1], nums[2]


def _drift_score(major: int, minor: int, patch: int) -> float:
    """Weighted drift score: majors count most, patches least."""
    return major * 10.0 + minor * 1.0 + patch * 0.1


def compute_drift(
    project: str, statuses: List[DependencyStatus]
) -> List[DriftEntry]:
    """Return a DriftEntry for every outdated dependency in *statuses*."""
    entries: List[DriftEntry] = []
    for s in statuses:
        if not s.is_outdated:
            continue
        cur = _parse(s.current_version)
        lat = _parse(s.latest_version)
        major_gap = max(lat[0] - cur[0], 0)
        minor_gap = max(lat[1] - cur[1], 0) if major_gap == 0 else 0
        patch_gap = max(lat[2] - cur[2], 0) if major_gap == 0 and minor_gap == 0 else 0
        entries.append(
            DriftEntry(
                project=project,
                package=s.package_name,
                current_version=s.current_version,
                latest_version=s.latest_version,
                major_gap=major_gap,
                minor_gap=minor_gap,
                patch_gap=patch_gap,
                drift_score=_drift_score(major_gap, minor_gap, patch_gap),
            )
        )
    entries.sort(key=lambda e: e.drift_score, reverse=True)
    return entries


def format_drift_report(entries: List[DriftEntry]) -> str:
    """Render a human-readable drift report."""
    if not entries:
        return "No drift detected — all dependencies are up to date."
    lines = ["Dependency Drift Report", "=" * 40]
    for e in entries:
        lines.append(
            f"  [{e.project}] {e.package}: {e.current_version} → {e.latest_version}  "
            f"(major+{e.major_gap} minor+{e.minor_gap} patch+{e.patch_gap}  score={e.drift_score:.1f})"
        )
    lines.append(f"\nTotal drifted packages: {len(entries)}")
    return "\n".join(lines)
