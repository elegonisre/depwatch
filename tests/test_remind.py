"""Tests for depwatch.remind."""
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from depwatch.remind import find_long_outdated, format_remind_report


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


def test_no_records_returns_empty(hist):
    _write_history(hist, [])
    result = find_long_outdated(str(hist), "myproject", min_days=7)
    assert result == []


def test_package_outdated_long_enough(hist):
    records = [
        {
            "project": "myproject",
            "timestamp": _ts(10),
            "dependencies": [
                {"name": "requests", "is_outdated": True, "current_version": "2.0", "latest_version": "2.28"}
            ],
        }
    ]
    _write_history(hist, records)
    result = find_long_outdated(str(hist), "myproject", min_days=7)
    assert len(result) == 1
    assert result[0].package == "requests"
    assert result[0].days_outdated >= 10


def test_package_not_outdated_long_enough(hist):
    records = [
        {
            "project": "myproject",
            "timestamp": _ts(3),
            "dependencies": [
                {"name": "flask", "is_outdated": True, "current_version": "1.0", "latest_version": "2.0"}
            ],
        }
    ]
    _write_history(hist, records)
    result = find_long_outdated(str(hist), "myproject", min_days=7)
    assert result == []


def test_package_reset_when_up_to_date(hist):
    records = [
        {
            "project": "myproject",
            "timestamp": _ts(20),
            "dependencies": [{"name": "django", "is_outdated": True, "current_version": "3.0", "latest_version": "4.0"}],
        },
        {
            "project": "myproject",
            "timestamp": _ts(5),
            "dependencies": [{"name": "django", "is_outdated": False, "current_version": "4.0", "latest_version": "4.0"}],
        },
    ]
    _write_history(hist, records)
    result = find_long_outdated(str(hist), "myproject", min_days=7)
    assert result == []


def test_format_remind_report_empty():
    msg = format_remind_report([])
    assert "No long-outdated" in msg


def test_format_remind_report_shows_entries(hist):
    records = [
        {
            "project": "proj",
            "timestamp": _ts(15),
            "dependencies": [
                {"name": "numpy", "is_outdated": True, "current_version": "1.0", "latest_version": "1.24"}
            ],
        }
    ]
    _write_history(hist, records)
    entries = find_long_outdated(str(hist), "proj", min_days=7)
    report = format_remind_report(entries)
    assert "numpy" in report
    assert "1.0" in report
    assert "1.24" in report
