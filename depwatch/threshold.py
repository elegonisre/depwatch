"""Threshold enforcement: fail or warn when outdated counts exceed configured limits."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from depwatch.checker import DependencyStatus


@dataclass
class ThresholdConfig:
    max_outdated: Optional[int] = None          # absolute count
    max_outdated_ratio: Optional[float] = None  # 0.0–1.0
    warn_outdated: Optional[int] = None         # warn-only count
    warn_ratio: Optional[float] = None          # warn-only ratio


@dataclass
class ThresholdResult:
    passed: bool
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)

    @property
    def has_warnings(self) -> bool:
        return bool(self.warnings)

    @property
    def has_errors(self) -> bool:
        return bool(self.errors)


def _outdated(statuses: List[DependencyStatus]) -> int:
    return sum(1 for s in statuses if s.is_outdated)


def evaluate_threshold(
    statuses: List[DependencyStatus],
    config: ThresholdConfig,
) -> ThresholdResult:
    """Evaluate statuses against threshold config and return a ThresholdResult."""
    total = len(statuses)
    outdated = _outdated(statuses)
    ratio = outdated / total if total > 0 else 0.0

    warnings: List[str] = []
    errors: List[str] = []

    if config.warn_outdated is not None and outdated >= config.warn_outdated:
        warnings.append(
            f"Outdated count {outdated} meets warn threshold {config.warn_outdated}."
        )

    if config.warn_ratio is not None and ratio >= config.warn_ratio:
        pct = f"{ratio:.0%}"
        warnings.append(
            f"Outdated ratio {pct} meets warn threshold {config.warn_ratio:.0%}."
        )

    if config.max_outdated is not None and outdated > config.max_outdated:
        errors.append(
            f"Outdated count {outdated} exceeds max_outdated={config.max_outdated}."
        )

    if config.max_outdated_ratio is not None and ratio > config.max_outdated_ratio:
        pct = f"{ratio:.0%}"
        errors.append(
            f"Outdated ratio {pct} exceeds max_outdated_ratio={config.max_outdated_ratio:.0%}."
        )

    return ThresholdResult(passed=not bool(errors), warnings=warnings, errors=errors)


def format_threshold_result(result: ThresholdResult) -> str:
    lines: List[str] = []
    for w in result.warnings:
        lines.append(f"[WARN]  {w}")
    for e in result.errors:
        lines.append(f"[ERROR] {e}")
    if not lines:
        lines.append("[OK]    All thresholds passed.")
    return "\n".join(lines)
