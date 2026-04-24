"""Quota tracking: enforce a maximum number of PyPI checks per run."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from depwatch.checker import DependencyStatus


@dataclass
class QuotaConfig:
    max_checks: int = 100  # maximum dependency checks allowed in one run
    warn_at: int = 80      # emit a warning when this many checks are reached


@dataclass
class QuotaResult:
    allowed: List[DependencyStatus] = field(default_factory=list)
    skipped: List[str] = field(default_factory=list)  # package names that were not checked
    warning: str = ""
    limit_reached: bool = False


def apply_quota(
    statuses: List[DependencyStatus],
    config: QuotaConfig,
) -> QuotaResult:
    """Trim *statuses* to honour *config.max_checks*.

    Packages beyond the limit are recorded as skipped.  A warning is set when
    the number of checks meets or exceeds *config.warn_at*.
    """
    result = QuotaResult()
    total = len(statuses)

    if total >= config.warn_at:
        result.warning = (
            f"Quota warning: {total} checks requested, warn threshold is {config.warn_at}."
        )

    if total > config.max_checks:
        result.allowed = statuses[: config.max_checks]
        result.skipped = [s.package for s in statuses[config.max_checks :]]
        result.limit_reached = True
    else:
        result.allowed = list(statuses)

    return result


def format_quota_report(result: QuotaResult) -> str:
    """Return a human-readable summary of quota usage."""
    lines: List[str] = []
    checked = len(result.allowed)
    skipped = len(result.skipped)

    lines.append(f"Checks performed : {checked}")
    if result.limit_reached:
        lines.append(f"Checks skipped   : {skipped} (quota exceeded)")
        lines.append(f"Skipped packages : {', '.join(result.skipped)}")
    if result.warning:
        lines.append(f"Warning          : {result.warning}")
    return "\n".join(lines)
