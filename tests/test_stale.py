"""Tests for depwatch.stale."""
from datetime import datetime, timedelta, timezone

import pytest

from depwatch.checker import DependencyStatus
from depwatch.stale import (
    StaleEntry,
    days_since,
    find_stale,
    format_stale_report,
)


def _s(package: str, current: str, latest: str, outdated: bool) -> DependencyStatus:
    return DependencyStatus(
        package=package,
        current_version=current,
        latest_version=latest,
        is_outdated=outdated,
    )


def test_days_since_past():
    past = datetime.now(tz=timezone.utc) - timedelta(days=5)
    assert days_since(past) == 5


def test_days_since_now():
    now = datetime.now(tz=timezone.utc)
    assert days_since(now) == 0


def test_days_since_naive_datetime():
    naive = datetime.utcnow() - timedelta(days=3)
    assert days_since(naive) == 3


def test_find_stale_returns_only_outdated():
    statuses = [
        _s("django", "3.0", "4.2", True),
        _s("requests", "2.28", "2.28", False),
    ]
    checked_at = datetime.now(tz=timezone.utc) - timedelta(days=10)
    entries = find_stale(statuses, "myapp", threshold_days=7, checked_at=checked_at)
    assert len(entries) == 1
    assert entries[0].package == "django"
    assert entries[0].project == "myapp"
    assert entries[0].days_outdated == 10


def test_find_stale_empty_when_none_outdated():
    statuses = [_s("requests", "2.28", "2.28", False)]
    entries = find_stale(statuses, "myapp", threshold_days=1)
    assert entries == []


def test_find_stale_defaults_checked_at_to_now():
    statuses = [_s("flask", "1.0", "2.0", True)]
    entries = find_stale(statuses, "proj", threshold_days=0)
    assert len(entries) == 1
    assert entries[0].days_outdated == 0


def test_format_stale_report_no_entries():
    result = format_stale_report([], threshold_days=7)
    assert "No dependencies" in result
    assert "7" in result


def test_format_stale_report_with_entries():
    entries = [
        StaleEntry(
            project="myapp",
            package="django",
            current_version="3.0",
            latest_version="4.2",
            days_outdated=10,
            is_outdated=True,
        )
    ]
    result = format_stale_report(entries, threshold_days=7)
    assert "django" in result
    assert "3.0" in result
    assert "4.2" in result
    assert "10d" in result
