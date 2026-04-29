"""Tests for depwatch.coverage."""
import pytest

from depwatch.checker import DependencyStatus
from depwatch.coverage import (
    CoverageReport,
    _grade,
    compute_coverage,
    format_coverage_report,
)


def _s(name: str, current: str, latest: str) -> DependencyStatus:
    return DependencyStatus(
        package=name,
        current_version=current,
        latest_version=latest,
        is_outdated=(current != latest),
    )


# ---------------------------------------------------------------------------
# _grade
# ---------------------------------------------------------------------------

def test_grade_a():
    assert _grade(100.0) == "A"
    assert _grade(95.0) == "A"


def test_grade_b():
    assert _grade(90.0) == "B"
    assert _grade(80.0) == "B"


def test_grade_c():
    assert _grade(70.0) == "C"
    assert _grade(60.0) == "C"


def test_grade_d():
    assert _grade(50.0) == "D"
    assert _grade(40.0) == "D"


def test_grade_f():
    assert _grade(39.9) == "F"
    assert _grade(0.0) == "F"


# ---------------------------------------------------------------------------
# compute_coverage
# ---------------------------------------------------------------------------

def test_full_coverage():
    statuses = [_s("requests", "2.0", "2.0"), _s("flask", "1.0", "2.0")]
    report = compute_coverage("myapp", ["requests", "flask"], statuses)
    assert report.total == 2
    assert report.monitored == 2
    assert report.unmonitored == []
    assert report.coverage_pct == 100.0
    assert report.grade == "A"


def test_partial_coverage():
    statuses = [_s("requests", "2.0", "2.0")]
    report = compute_coverage("myapp", ["requests", "flask", "django"], statuses)
    assert report.monitored == 1
    assert report.total == 3
    assert set(report.unmonitored) == {"flask", "django"}
    assert report.coverage_pct == pytest.approx(33.3, abs=0.1)
    assert report.grade == "F"


def test_no_deps_returns_full_coverage():
    report = compute_coverage("empty", [], [])
    assert report.coverage_pct == 100.0
    assert report.grade == "A"


# ---------------------------------------------------------------------------
# format_coverage_report
# ---------------------------------------------------------------------------

def test_format_empty():
    assert format_coverage_report([]) == "No coverage data available."


def test_format_shows_project_name():
    r = compute_coverage("myapp", ["requests"], [_s("requests", "2.0", "2.0")])
    out = format_coverage_report([r])
    assert "myapp" in out
    assert "100.0%" in out


def test_format_lists_unmonitored():
    r = compute_coverage("proj", ["requests", "flask"], [_s("requests", "2.0", "2.0")])
    out = format_coverage_report([r])
    assert "flask" in out
    assert "Unmonitored" in out
