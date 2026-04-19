"""Tests for depwatch.outdated_age."""
from __future__ import annotations

import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from depwatch.outdated_age import OutdatedAge, compute_outdated_ages, format_age_report


def _ts(days_ago: int) -> str:
    dt = datetime.now(timezone.utc) - timedelta(days=days_ago)
    return dt.isoformat()


def _write_history(path: Path, records: list) -> None:
    with open(path, "w") as f:
        for rec in records:
            f.write(json.dumps(rec) + "\n")


@pytest.fixture
def hist(tmp_path):
    return tmp_path / "history.jsonl"


def test_no_history_returns_empty(hist):
    result = compute_outdated_ages(str(hist))
    assert result == []


def test_single_outdated_package(hist):
    _write_history(hist, [
        {
            "project": "myapp",
            "timestamp": _ts(10),
            "dependencies": [
                {"package": "requests", "is_outdated": True,
                 "current_version": "2.27.0", "latest_version": "2.31.0"},
            ],
        }
    ])
    result = compute_outdated_ages(str(hist))
    assert len(result) == 1
    assert result[0].package == "requests"
    assert result[0].days_outdated >= 10


def test_up_to_date_package_excluded(hist):
    _write_history(hist, [
        {
            "project": "myapp",
            "timestamp": _ts(5),
            "dependencies": [
                {"package": "flask", "is_outdated": False,
                 "current_version": "2.3.0", "latest_version": "2.3.0"},
            ],
        }
    ])
    result = compute_outdated_ages(str(hist))
    assert result == []


def test_first_seen_is_earliest(hist):
    _write_history(hist, [
        {"project": "p", "timestamp": _ts(20), "dependencies": [
            {"package": "django", "is_outdated": True,
             "current_version": "3.0", "latest_version": "4.2"},
        ]},
        {"project": "p", "timestamp": _ts(5), "dependencies": [
            {"package": "django", "is_outdated": True,
             "current_version": "3.0", "latest_version": "4.2"},
        ]},
    ])
    result = compute_outdated_ages(str(hist))
    assert len(result) == 1
    assert result[0].days_outdated >= 20


def test_filter_by_project(hist):
    _write_history(hist, [
        {"project": "alpha", "timestamp": _ts(3), "dependencies": [
            {"package": "numpy", "is_outdated": True,
             "current_version": "1.0", "latest_version": "2.0"},
        ]},
        {"project": "beta", "timestamp": _ts(3), "dependencies": [
            {"package": "scipy", "is_outdated": True,
             "current_version": "1.0", "latest_version": "2.0"},
        ]},
    ])
    result = compute_outdated_ages(str(hist), project="alpha")
    assert all(e.project == "alpha" for e in result)
    assert len(result) == 1


def test_format_age_report_empty():
    assert "No outdated" in format_age_report([])


def test_format_age_report_contains_package():
    entry = OutdatedAge(
        project="myapp", package="requests",
        first_seen_outdated=datetime.now(timezone.utc) - timedelta(days=7),
        days_outdated=7, current_version="2.27.0", latest_version="2.31.0",
    )
    report = format_age_report([entry])
    assert "requests" in report
    assert "7 day" in report
