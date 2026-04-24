"""Tests for depwatch.threshold."""
from __future__ import annotations

import pytest

from depwatch.checker import DependencyStatus
from depwatch.threshold import (
    ThresholdConfig,
    ThresholdResult,
    evaluate_threshold,
    format_threshold_result,
)


def _s(name: str, is_outdated: bool) -> DependencyStatus:
    return DependencyStatus(
        name=name,
        current_version="1.0.0",
        latest_version="2.0.0" if is_outdated else "1.0.0",
        is_outdated=is_outdated,
    )


STATUSES = [_s("a", True), _s("b", False), _s("c", False), _s("d", True)]


def test_no_thresholds_always_passes():
    result = evaluate_threshold(STATUSES, ThresholdConfig())
    assert result.passed
    assert not result.warnings
    assert not result.errors


def test_max_outdated_passes_when_under():
    result = evaluate_threshold(STATUSES, ThresholdConfig(max_outdated=3))
    assert result.passed
    assert not result.errors


def test_max_outdated_fails_when_over():
    result = evaluate_threshold(STATUSES, ThresholdConfig(max_outdated=1))
    assert not result.passed
    assert len(result.errors) == 1
    assert "max_outdated=1" in result.errors[0]


def test_max_ratio_fails_when_over():
    # 2/4 = 50% > 40%
    result = evaluate_threshold(STATUSES, ThresholdConfig(max_outdated_ratio=0.4))
    assert not result.passed
    assert result.has_errors


def test_max_ratio_passes_when_equal_boundary():
    # 2/4 = 50%, threshold 50% — strictly greater fails only
    result = evaluate_threshold(STATUSES, ThresholdConfig(max_outdated_ratio=0.5))
    assert result.passed


def test_warn_outdated_produces_warning_not_error():
    result = evaluate_threshold(STATUSES, ThresholdConfig(warn_outdated=2))
    assert result.passed
    assert result.has_warnings
    assert not result.has_errors


def test_warn_ratio_produces_warning():
    result = evaluate_threshold(STATUSES, ThresholdConfig(warn_ratio=0.4))
    assert result.passed
    assert result.has_warnings


def test_empty_statuses_passes_all():
    result = evaluate_threshold([], ThresholdConfig(max_outdated=0, max_outdated_ratio=0.0))
    assert result.passed


def test_format_result_ok():
    result = ThresholdResult(passed=True)
    text = format_threshold_result(result)
    assert "[OK]" in text


def test_format_result_with_warn_and_error():
    result = ThresholdResult(
        passed=False,
        warnings=["warn msg"],
        errors=["err msg"],
    )
    text = format_threshold_result(result)
    assert "[WARN]" in text
    assert "[ERROR]" in text
    assert "warn msg" in text
    assert "err msg" in text
