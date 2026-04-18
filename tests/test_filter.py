"""Tests for depwatch.filter."""
import pytest
from depwatch.checker import DependencyStatus
from depwatch.filter import (
    filter_outdated,
    filter_by_name,
    filter_by_project,
    filter_min_versions_behind,
    apply_ignore_list,
)


def _s(name, current, latest):
    return DependencyStatus(
        name=name,
        current_version=current,
        latest_version=latest,
        is_outdated=current != latest,
    )


STATUSES = [
    _s("requests", "2.28.0", "2.31.0"),
    _s("flask", "2.0.0", "2.0.0"),
    _s("django", "3.2.0", "5.0.0"),
    _s("numpy", "1.24.0", "1.26.0"),
]


def test_filter_outdated():
    result = filter_outdated(STATUSES)
    names = [s.name for s in result]
    assert "requests" in names
    assert "django" in names
    assert "flask" not in names


def test_filter_by_name():
    result = filter_by_name(STATUSES, ["Flask", "numpy"])
    names = [s.name for s in result]
    assert set(names) == {"flask", "numpy"}


def test_filter_by_name_empty():
    assert filter_by_name(STATUSES, []) == []


def test_filter_by_project():
    records = [
        {"project": "alpha", "data": 1},
        {"project": "Beta", "data": 2},
        {"project": "alpha", "data": 3},
    ]
    result = filter_by_project(records, "alpha")
    assert len(result) == 2
    result2 = filter_by_project(records, "beta")
    assert len(result2) == 1


def test_filter_min_versions_behind_major():
    # django 3 -> 5 is 2 major versions behind
    result = filter_min_versions_behind(STATUSES, min_behind=2)
    names = [s.name for s in result]
    assert "django" in names
    assert "requests" not in names  # same major
    assert "numpy" not in names


def test_filter_min_versions_behind_zero():
    result = filter_min_versions_behind(STATUSES, min_behind=0)
    # all outdated qualify
    names = [s.name for s in result]
    assert set(names) == {"requests", "django", "numpy"}


def test_apply_ignore_list():
    result = apply_ignore_list(STATUSES, ["requests", "FLASK"])
    names = [s.name for s in result]
    assert "requests" not in names
    assert "flask" not in names
    assert "django" in names


def test_apply_ignore_list_none():
    result = apply_ignore_list(STATUSES, None)
    assert result == STATUSES
