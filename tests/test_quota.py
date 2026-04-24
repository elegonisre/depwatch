"""Tests for depwatch.quota."""
from __future__ import annotations

import pytest

from depwatch.checker import DependencyStatus
from depwatch.quota import QuotaConfig, QuotaResult, apply_quota, format_quota_report


def _s(name: str, outdated: bool = True) -> DependencyStatus:
    return DependencyStatus(
        package=name,
        current_version="1.0.0",
        latest_version="2.0.0" if outdated else "1.0.0",
        is_outdated=outdated,
        project="proj",
    )


def _statuses(n: int) -> list[DependencyStatus]:
    return [_s(f"pkg{i}") for i in range(n)]


# ---------------------------------------------------------------------------
# apply_quota
# ---------------------------------------------------------------------------

def test_under_limit_returns_all():
    cfg = QuotaConfig(max_checks=10, warn_at=8)
    statuses = _statuses(5)
    result = apply_quota(statuses, cfg)
    assert len(result.allowed) == 5
    assert result.skipped == []
    assert result.limit_reached is False


def test_exactly_at_limit_not_exceeded():
    cfg = QuotaConfig(max_checks=5, warn_at=4)
    statuses = _statuses(5)
    result = apply_quota(statuses, cfg)
    assert len(result.allowed) == 5
    assert result.limit_reached is False


def test_over_limit_truncates_and_records_skipped():
    cfg = QuotaConfig(max_checks=3, warn_at=10)
    statuses = _statuses(6)
    result = apply_quota(statuses, cfg)
    assert len(result.allowed) == 3
    assert len(result.skipped) == 3
    assert result.skipped == ["pkg3", "pkg4", "pkg5"]
    assert result.limit_reached is True


def test_warn_at_threshold_sets_warning():
    cfg = QuotaConfig(max_checks=100, warn_at=3)
    statuses = _statuses(3)
    result = apply_quota(statuses, cfg)
    assert result.warning != ""
    assert "warn threshold" in result.warning


def test_below_warn_threshold_no_warning():
    cfg = QuotaConfig(max_checks=100, warn_at=10)
    statuses = _statuses(5)
    result = apply_quota(statuses, cfg)
    assert result.warning == ""


def test_empty_statuses():
    cfg = QuotaConfig(max_checks=10, warn_at=8)
    result = apply_quota([], cfg)
    assert result.allowed == []
    assert result.skipped == []
    assert result.limit_reached is False


# ---------------------------------------------------------------------------
# format_quota_report
# ---------------------------------------------------------------------------

def test_format_report_no_skip():
    result = QuotaResult(allowed=_statuses(3))
    report = format_quota_report(result)
    assert "3" in report
    assert "skipped" not in report.lower()


def test_format_report_with_skip():
    result = QuotaResult(
        allowed=_statuses(3),
        skipped=["pkgA", "pkgB"],
        limit_reached=True,
    )
    report = format_quota_report(result)
    assert "pkgA" in report
    assert "pkgB" in report
    assert "quota exceeded" in report


def test_format_report_shows_warning():
    result = QuotaResult(
        allowed=_statuses(2),
        warning="Quota warning: 2 checks requested, warn threshold is 2.",
    )
    report = format_quota_report(result)
    assert "Warning" in report
