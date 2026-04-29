"""Tests for depwatch.staleness_index."""

from __future__ import annotations

import pytest

from depwatch.checker import DependencyStatus
from depwatch.staleness_index import (
    StalenessIndex,
    _staleness_label,
    _version_gap,
    compute_staleness_index,
    format_staleness_report,
)


def _s(name: str, current: str, latest: str, outdated: bool) -> DependencyStatus:
    return DependencyStatus(
        package=name,
        current_version=current,
        latest_version=latest,
        is_outdated=outdated,
        project="proj",
    )


# ---------------------------------------------------------------------------
# _version_gap
# ---------------------------------------------------------------------------

def test_version_gap_major():
    assert _version_gap("1.0.0", "3.0.0") == (2, 0)


def test_version_gap_minor_only():
    assert _version_gap("1.2.0", "1.5.0") == (0, 3)


def test_version_gap_same():
    assert _version_gap("2.3.1", "2.3.1") == (0, 0)


def test_version_gap_short_version():
    assert _version_gap("1", "3") == (2, 0)


# ---------------------------------------------------------------------------
# _staleness_label
# ---------------------------------------------------------------------------

def test_staleness_label_low():
    assert _staleness_label(10) == "low"


def test_staleness_label_moderate():
    assert _staleness_label(30) == "moderate"


def test_staleness_label_high():
    assert _staleness_label(55) == "high"


def test_staleness_label_critical():
    assert _staleness_label(80) == "critical"


# ---------------------------------------------------------------------------
# compute_staleness_index
# ---------------------------------------------------------------------------

def test_compute_empty_returns_zero_score():
    result = compute_staleness_index("myproject", [])
    assert result.score == 0.0
    assert result.label == "low"
    assert result.total == 0


def test_compute_all_up_to_date():
    statuses = [
        _s("requests", "2.28.0", "2.28.0", False),
        _s("flask", "2.3.0", "2.3.0", False),
    ]
    result = compute_staleness_index("myproject", statuses)
    assert result.score == 0.0
    assert result.outdated == 0


def test_compute_all_outdated_major_gap():
    statuses = [
        _s("django", "2.0.0", "4.0.0", True),
        _s("flask", "1.0.0", "3.0.0", True),
    ]
    result = compute_staleness_index("myproject", statuses)
    assert result.score > 50
    assert result.outdated == 2
    assert result.avg_major_gap == 2.0


def test_compute_partial_outdated():
    statuses = [
        _s("requests", "2.28.0", "2.28.0", False),
        _s("django", "3.0.0", "4.0.0", True),
    ]
    result = compute_staleness_index("myproject", statuses)
    assert 0 < result.score < 100
    assert result.outdated == 1
    assert result.total == 2


def test_compute_score_capped_at_100():
    # Extreme gap — score must not exceed 100
    statuses = [_s(f"pkg{i}", "1.0.0", "99.0.0", True) for i in range(10)]
    result = compute_staleness_index("bigproject", statuses)
    assert result.score <= 100.0


# ---------------------------------------------------------------------------
# format_staleness_report
# ---------------------------------------------------------------------------

def test_format_no_entries():
    assert format_staleness_report([]) == "No data available."


def test_format_shows_project_name():
    entry = StalenessIndex(
        project="alpha", total=5, outdated=2,
        avg_major_gap=1.0, avg_minor_gap=0.5, score=30.0, label="moderate"
    )
    report = format_staleness_report([entry])
    assert "alpha" in report
    assert "MODERATE" in report
    assert "30.0/100" in report


def test_format_sorted_descending():
    entries = [
        StalenessIndex("low", 3, 0, 0.0, 0.0, 5.0, "low"),
        StalenessIndex("high", 3, 3, 2.0, 0.0, 80.0, "critical"),
    ]
    report = format_staleness_report(entries)
    assert report.index("high") < report.index("low")
