"""Tests for depwatch.maturity."""

from __future__ import annotations

import pytest

from depwatch.checker import DependencyStatus
from depwatch.maturity import (
    MaturityEntry,
    _maturity_label,
    _parse_major,
    compute_maturity,
    format_maturity_report,
)


def _s(
    package: str,
    current: str,
    latest: str,
    outdated: bool = True,
) -> DependencyStatus:
    return DependencyStatus(
        package=package,
        current_version=current,
        latest_version=latest,
        is_outdated=outdated,
    )


# ---------------------------------------------------------------------------
# _parse_major
# ---------------------------------------------------------------------------

def test_parse_major_normal():
    assert _parse_major("3.1.4") == 3


def test_parse_major_single_segment():
    assert _parse_major("2") == 2


def test_parse_major_invalid():
    assert _parse_major("unknown") == 0


def test_parse_major_empty():
    assert _parse_major("") == 0


# ---------------------------------------------------------------------------
# _maturity_label
# ---------------------------------------------------------------------------

def test_label_stable():
    assert _maturity_label(0.9) == "stable"


def test_label_maturing():
    assert _maturity_label(0.6) == "maturing"


def test_label_young():
    assert _maturity_label(0.3) == "young"


def test_label_legacy():
    assert _maturity_label(0.1) == "legacy"


# ---------------------------------------------------------------------------
# compute_maturity
# ---------------------------------------------------------------------------

def test_compute_maturity_returns_one_entry_per_status():
    statuses = [_s("django", "3.2", "4.2"), _s("requests", "2.28.0", "2.31.0")]
    entries = compute_maturity(statuses, project="myapp")
    assert len(entries) == 2


def test_compute_maturity_project_name_propagated():
    entries = compute_maturity([_s("flask", "2.0", "3.0")], project="webapp")
    assert entries[0].project == "webapp"


def test_compute_maturity_up_to_date_no_penalty():
    entries = compute_maturity([_s("click", "8.1", "8.1", outdated=False)])
    e = entries[0]
    assert e.versions_behind == 0
    assert e.is_outdated is False
    # score should be positive for major version 8
    assert e.maturity_score > 0


def test_compute_maturity_large_gap_reduces_score():
    up_to_date = compute_maturity([_s("lib", "5.0", "5.0", outdated=False)])[0]
    outdated = compute_maturity([_s("lib", "1.0", "5.0", outdated=True)])[0]
    assert outdated.maturity_score < up_to_date.maturity_score


def test_compute_maturity_score_clamped_to_zero():
    # Extreme gap should not produce negative score
    entries = compute_maturity([_s("oldlib", "0.1", "1.0", outdated=True)])
    assert entries[0].maturity_score >= 0.0


def test_compute_maturity_empty_returns_empty():
    assert compute_maturity([]) == []


# ---------------------------------------------------------------------------
# format_maturity_report
# ---------------------------------------------------------------------------

def test_format_report_no_data():
    result = format_maturity_report([])
    assert "No dependency" in result


def test_format_report_contains_package_name():
    entries = compute_maturity([_s("requests", "2.28.0", "2.31.0")])
    report = format_maturity_report(entries)
    assert "requests" in report


def test_format_report_contains_average():
    entries = compute_maturity([_s("flask", "2.0", "3.0")])
    report = format_maturity_report(entries)
    assert "Average maturity score" in report
