"""Tests for depwatch.groupby."""
import pytest
from depwatch.checker import DependencyStatus
from depwatch.groupby import (
    group_by_project,
    group_by_status,
    group_by_major_version_gap,
    summary,
)


def _s(name, current, latest, project="proj"):
    return DependencyStatus(
        package=name,
        current_version=current,
        latest_version=latest,
        is_outdated=current != latest,
        project=project,
    )


def test_group_by_project():
    statuses = [_s("flask", "2.0", "2.1", "web"), _s("django", "3.0", "4.0", "api"), _s("requests", "2.0", "2.0", "web")]
    groups = group_by_project(statuses)
    assert set(groups.keys()) == {"web", "api"}
    assert len(groups["web"]) == 2
    assert len(groups["api"]) == 1


def test_group_by_project_empty():
    assert group_by_project([]) == {}


def test_group_by_status_splits_correctly():
    statuses = [_s("flask", "2.0", "2.1"), _s("requests", "2.0", "2.0")]
    groups = group_by_status(statuses)
    assert len(groups["outdated"]) == 1
    assert groups["outdated"][0].package == "flask"
    assert len(groups["up_to_date"]) == 1


def test_group_by_status_all_up_to_date():
    statuses = [_s("a", "1.0", "1.0"), _s("b", "2.0", "2.0")]
    groups = group_by_status(statuses)
    assert groups["outdated"] == []
    assert len(groups["up_to_date"]) == 2


def test_group_by_major_version_gap():
    statuses = [
        _s("a", "1.0", "1.5"),   # gap 0 -> none
        _s("b", "1.0", "2.0"),   # gap 1 -> one
        _s("c", "1.0", "3.0"),   # gap 2 -> multiple
        _s("d", "1.0", "1.0"),   # not outdated -> none
    ]
    groups = group_by_major_version_gap(statuses)
    assert len(groups["none"]) == 2
    assert len(groups["one"]) == 1
    assert len(groups["multiple"]) == 1


def test_summary_counts():
    statuses = [_s("a", "1.0", "2.0"), _s("b", "1.0", "1.0"), _s("c", "2.0", "3.0")]
    result = summary(statuses)
    assert result["total"] == 3
    assert result["outdated"] == 2
    assert result["up_to_date"] == 1


def test_summary_empty():
    result = summary([])
    assert result == {"total": 0, "outdated": 0, "up_to_date": 0}
