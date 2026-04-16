"""Tests for depwatch.trend analysis helpers."""

from depwatch.trend import (
    outdated_counts_over_time,
    most_frequently_outdated,
    latest_snapshot,
)


def _rec(project, package, outdated, checked_at):
    return {
        "project": project,
        "package": package,
        "current_version": "1.0",
        "latest_version": "2.0",
        "outdated": outdated,
        "checked_at": checked_at,
    }


RECORDS = [
    _rec("proj_a", "requests", True, "2024-01-01T00:00:00"),
    _rec("proj_a", "flask", True, "2024-01-01T00:00:00"),
    _rec("proj_a", "requests", True, "2024-01-02T00:00:00"),
    _rec("proj_a", "flask", False, "2024-01-02T00:00:00"),
    _rec("proj_b", "django", True, "2024-01-01T00:00:00"),
]


def test_outdated_counts_over_time():
    counts = outdated_counts_over_time(RECORDS)
    assert counts["2024-01-01T00:00:00"] == 3
    assert counts["2024-01-02T00:00:00"] == 1


def test_outdated_counts_no_outdated():
    counts = outdated_counts_over_time([_rec("p", "pkg", False, "2024-01-01T00:00:00")])
    assert counts == {}


def test_most_frequently_outdated():
    result = most_frequently_outdated(RECORDS)
    assert result[0]["package"] == "requests"
    assert result[0]["outdated_count"] == 2


def test_most_frequently_outdated_top_n():
    result = most_frequently_outdated(RECORDS, top_n=1)
    assert len(result) == 1


def test_latest_snapshot_returns_most_recent(tmp_path):
    result = latest_snapshot(RECORDS, "proj_a")
    by_pkg = {r["package"]: r for r in result}
    assert by_pkg["requests"]["checked_at"] == "2024-01-02T00:00:00"
    assert by_pkg["flask"]["checked_at"] == "2024-01-02T00:00:00"


def test_latest_snapshot_filters_project():
    result = latest_snapshot(RECORDS, "proj_b")
    assert all(r["project"] == "proj_b" for r in result)
    assert len(result) == 1
