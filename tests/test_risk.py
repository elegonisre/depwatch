"""Tests for depwatch.risk module."""
import pytest
from depwatch.checker import DependencyStatus
from depwatch.risk import (
    _version_parts, _compute_gaps, _risk_score, _risk_label,
    assess_risk, format_risk_report, RiskEntry,
)


def _s(pkg, current, latest, outdated=True):
    return DependencyStatus(package=pkg, current_version=current, latest_version=latest, is_outdated=outdated)


def test_version_parts_normal():
    assert _version_parts("1.2.3") == [1, 2, 3]


def test_version_parts_short():
    assert _version_parts("2.0") == [2, 0, 0]


def test_compute_gaps_major():
    major, minor = _compute_gaps("1.0.0", "3.0.0")
    assert major == 2
    assert minor == 0


def test_compute_gaps_minor_only():
    major, minor = _compute_gaps("1.2.0", "1.5.0")
    assert major == 0
    assert minor == 3


def test_compute_gaps_minor_ignored_when_major_diff():
    major, minor = _compute_gaps("1.9.0", "2.1.0")
    assert major == 1
    assert minor == 0


def test_risk_score_no_gap():
    assert _risk_score(0, 0) == 0.0


def test_risk_score_capped_at_one():
    assert _risk_score(10, 0) == 1.0


def test_risk_label_critical():
    assert _risk_label(0.9) == "critical"


def test_risk_label_high():
    assert _risk_label(0.6) == "high"


def test_risk_label_medium():
    assert _risk_label(0.3) == "medium"


def test_risk_label_low():
    assert _risk_label(0.0) == "low"


def test_assess_risk_skips_up_to_date():
    statuses = [_s("requests", "2.0.0", "2.0.0", outdated=False)]
    entries = assess_risk("myapp", statuses)
    assert entries == []


def test_assess_risk_returns_entry():
    statuses = [_s("django", "2.0.0", "4.0.0")]
    entries = assess_risk("myapp", statuses)
    assert len(entries) == 1
    e = entries[0]
    assert e.package == "django"
    assert e.major_gap == 2
    assert e.risk_label in ("high", "critical")


def test_assess_risk_sorted_by_score_desc():
    statuses = [
        _s("minor-pkg", "1.0.0", "1.1.0"),
        _s("major-pkg", "1.0.0", "4.0.0"),
    ]
    entries = assess_risk("proj", statuses)
    assert entries[0].package == "major-pkg"


def test_format_risk_report_empty():
    assert "No risk" in format_risk_report([])


def test_format_risk_report_contains_package():
    statuses = [_s("flask", "0.12.0", "3.0.0")]
    entries = assess_risk("web", statuses)
    report = format_risk_report(entries)
    assert "flask" in report
    assert "web" in report
