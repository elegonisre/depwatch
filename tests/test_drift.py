"""Tests for depwatch.drift."""
from __future__ import annotations

import pytest

from depwatch.checker import DependencyStatus
from depwatch.drift import (
    DriftEntry,
    _drift_score,
    _parse,
    compute_drift,
    format_drift_report,
)


def _s(pkg: str, current: str, latest: str, outdated: bool = True) -> DependencyStatus:
    return DependencyStatus(
        package_name=pkg,
        current_version=current,
        latest_version=latest,
        is_outdated=outdated,
    )


# --- _parse ---

def test_parse_normal():
    assert _parse("1.2.3") == (1, 2, 3)


def test_parse_short():
    assert _parse("2.0") == (2, 0, 0)


def test_parse_prerelease():
    major, minor, patch = _parse("3.1.0rc1")
    assert major == 3 and minor == 1 and patch == 0


# --- _drift_score ---

def test_drift_score_major_dominates():
    assert _drift_score(1, 0, 0) > _drift_score(0, 9, 9)


def test_drift_score_zero():
    assert _drift_score(0, 0, 0) == 0.0


# --- compute_drift ---

def test_compute_drift_skips_up_to_date():
    statuses = [_s("requests", "2.28.0", "2.28.0", outdated=False)]
    entries = compute_drift("myproject", statuses)
    assert entries == []


def test_compute_drift_major_gap():
    statuses = [_s("django", "3.2.0", "5.0.0")]
    entries = compute_drift("myproject", statuses)
    assert len(entries) == 1
    e = entries[0]
    assert e.major_gap == 2
    assert e.minor_gap == 0
    assert e.patch_gap == 0
    assert e.drift_score == pytest.approx(20.0)


def test_compute_drift_minor_gap_only():
    statuses = [_s("flask", "2.1.0", "2.4.0")]
    entries = compute_drift("myproject", statuses)
    e = entries[0]
    assert e.major_gap == 0
    assert e.minor_gap == 3
    assert e.patch_gap == 0
    assert e.drift_score == pytest.approx(3.0)


def test_compute_drift_sorted_descending():
    statuses = [
        _s("flask", "2.1.0", "2.4.0"),   # minor gap → score 3.0
        _s("django", "3.0.0", "5.0.0"),  # major gap → score 20.0
    ]
    entries = compute_drift("proj", statuses)
    assert entries[0].package == "django"
    assert entries[1].package == "flask"


def test_compute_drift_sets_project_name():
    statuses = [_s("boto3", "1.0.0", "1.2.0")]
    entries = compute_drift("aws-project", statuses)
    assert entries[0].project == "aws-project"


# --- format_drift_report ---

def test_format_drift_report_empty():
    report = format_drift_report([])
    assert "up to date" in report.lower()


def test_format_drift_report_contains_package():
    entries = compute_drift("proj", [_s("requests", "2.0.0", "2.3.0")])
    report = format_drift_report(entries)
    assert "requests" in report
    assert "2.0.0" in report
    assert "2.3.0" in report


def test_format_drift_report_summary_count():
    statuses = [_s("a", "1.0.0", "2.0.0"), _s("b", "1.0.0", "1.1.0")]
    entries = compute_drift("proj", statuses)
    report = format_drift_report(entries)
    assert "2" in report
