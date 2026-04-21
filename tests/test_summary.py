"""Tests for depwatch.summary."""

from __future__ import annotations

from depwatch.checker import DependencyStatus
from depwatch.summary import (
    ProjectSummary,
    _grade,
    summarise_project,
    summarise_all,
    format_summary,
)


def _s(name: str, current: str, latest: str, outdated: bool) -> DependencyStatus:
    return DependencyStatus(
        name=name,
        current_version=current,
        latest_version=latest,
        is_outdated=outdated,
    )


# --- _grade ---

def test_grade_zero():
    assert _grade(0.0) == "A"


def test_grade_low():
    assert _grade(0.05) == "B"


def test_grade_mid():
    assert _grade(0.20) == "C"


def test_grade_high():
    assert _grade(0.40) == "D"


def test_grade_critical():
    assert _grade(0.75) == "F"


# --- summarise_project ---

def test_summarise_project_all_up_to_date():
    statuses = [_s("requests", "2.0", "2.0", False), _s("flask", "3.0", "3.0", False)]
    result = summarise_project("myapp", statuses)
    assert result.total == 2
    assert result.outdated == 0
    assert result.up_to_date == 2
    assert result.outdated_ratio == 0.0
    assert result.grade == "A"
    assert result.project == "myapp"


def test_summarise_project_some_outdated():
    statuses = [
        _s("requests", "1.0", "2.0", True),
        _s("flask", "3.0", "3.0", False),
        _s("django", "3.0", "4.0", True),
        _s("click", "8.0", "8.0", False),
    ]
    result = summarise_project("proj", statuses)
    assert result.total == 4
    assert result.outdated == 2
    assert result.up_to_date == 2
    assert result.outdated_ratio == 0.5
    assert result.grade == "D"


def test_summarise_project_empty():
    result = summarise_project("empty", [])
    assert result.total == 0
    assert result.outdated == 0
    assert result.outdated_ratio == 0.0
    assert result.grade == "A"


# --- summarise_all ---

def test_summarise_all_sorted_by_ratio_desc():
    results = {
        "good": [_s("a", "1", "1", False)],
        "bad": [_s("b", "1", "2", True), _s("c", "1", "2", True)],
        "mid": [_s("d", "1", "2", True), _s("e", "1", "1", False)],
    }
    summaries = summarise_all(results)
    assert [s.project for s in summaries] == ["bad", "mid", "good"]


# --- format_summary ---

def test_format_summary_empty():
    assert format_summary([]) == "No projects to summarise."


def test_format_summary_contains_project_name():
    statuses = [_s("requests", "2.0", "2.0", False)]
    summaries = summarise_all({"myproject": statuses})
    output = format_summary(summaries)
    assert "myproject" in output


def test_format_summary_shows_totals_row():
    results = {
        "a": [_s("x", "1", "2", True)],
        "b": [_s("y", "1", "1", False)],
    }
    summaries = summarise_all(results)
    output = format_summary(summaries)
    assert "TOTAL" in output
