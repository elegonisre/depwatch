"""Policy enforcement: fail if outdated count or ratio exceeds thresholds."""
from __future__ import annotations
from dataclasses import dataclass
from typing import List
from depwatch.checker import DependencyStatus


@dataclass
class PolicyResult:
    passed: bool
    reason: str


@dataclass
class Policy:
    max_outdated: int | None = None        # absolute count
    max_outdated_ratio: float | None = None  # 0.0-1.0
    block_major_behind: int | None = None  # fail if any pkg N+ majors behind


def _outdated(statuses: List[DependencyStatus]) -> List[DependencyStatus]:
    return [s for s in statuses if s.is_outdated]


def evaluate_policy(policy: Policy, statuses: List[DependencyStatus]) -> PolicyResult:
    if not statuses:
        return PolicyResult(passed=True, reason="No dependencies to check.")

    outdated = _outdated(statuses)
    count = len(outdated)
    ratio = count / len(statuses)

    if policy.max_outdated is not None and count > policy.max_outdated:
        return PolicyResult(
            passed=False,
            reason=f"Outdated count {count} exceeds max_outdated={policy.max_outdated}.",
        )

    if policy.max_outdated_ratio is not None and ratio > policy.max_outdated_ratio:
        pct = f"{ratio:.0%}"
        limit = f"{policy.max_outdated_ratio:.0%}"
        return PolicyResult(
            passed=False,
            reason=f"Outdated ratio {pct} exceeds max_outdated_ratio={limit}.",
        )

    if policy.block_major_behind is not None:
        for s in outdated:
            try:
                cur_major = int(s.current_version.split(".")[0])
                lat_major = int(s.latest_version.split(".")[0])
                gap = lat_major - cur_major
                if gap >= policy.block_major_behind:
                    return PolicyResult(
                        passed=False,
                        reason=(
                            f"{s.package} is {gap} major version(s) behind "
                            f"(block_major_behind={policy.block_major_behind})."
                        ),
                    )
            except (ValueError, IndexError):
                continue

    return PolicyResult(passed=True, reason="All policy checks passed.")
