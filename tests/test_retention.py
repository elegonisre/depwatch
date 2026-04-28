"""Tests for depwatch.retention."""
from __future__ import annotations

import json
from datetime import datetime, timezone, timedelta
from pathlib import Path

import pytest

from depwatch.retention import apply_retention, format_retention_report, RetentionResult


def _ts(days_ago: int) -> str:
    dt = datetime.now(timezone.utc) - timedelta(days=days_ago)
    return dt.isoformat()


def _write_history(path: Path, records: list) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as fh:
        json.dump(records, fh)


@pytest.fixture()
def hist(tmp_path: Path) -> Path:
    return tmp_path / "depwatch_history.json"


def test_no_history_file_returns_zero_removed(hist: Path) -> None:
    result = apply_retention(max_days=30, history_file=hist)
    assert result.total_before == 0
    assert result.removed == 0
    assert result.total_after == 0


def test_all_recent_records_kept(hist: Path) -> None:
    records = [
        {"timestamp": _ts(1), "project": "a"},
        {"timestamp": _ts(5), "project": "b"},
    ]
    _write_history(hist, records)
    result = apply_retention(max_days=30, history_file=hist)
    assert result.removed == 0
    assert result.total_after == 2


def test_old_records_are_pruned(hist: Path) -> None:
    records = [
        {"timestamp": _ts(100), "project": "old"},
        {"timestamp": _ts(10), "project": "new"},
    ]
    _write_history(hist, records)
    result = apply_retention(max_days=30, history_file=hist)
    assert result.removed == 1
    assert result.total_after == 1


def test_all_old_records_removed(hist: Path) -> None:
    records = [
        {"timestamp": _ts(200), "project": "x"},
        {"timestamp": _ts(150), "project": "y"},
    ]
    _write_history(hist, records)
    result = apply_retention(max_days=30, history_file=hist)
    assert result.removed == 2
    assert result.total_after == 0


def test_malformed_timestamp_entry_kept(hist: Path) -> None:
    records = [
        {"timestamp": "not-a-date", "project": "bad"},
        {"timestamp": _ts(200), "project": "old"},
    ]
    _write_history(hist, records)
    result = apply_retention(max_days=30, history_file=hist)
    # malformed entry kept, old entry removed
    assert result.total_after == 1
    assert result.removed == 1


def test_invalid_max_days_raises(hist: Path) -> None:
    with pytest.raises(ValueError):
        apply_retention(max_days=0, history_file=hist)


def test_format_retention_report() -> None:
    result = RetentionResult(total_before=10, total_after=7, removed=3)
    report = format_retention_report(result)
    assert "10" in report
    assert "3" in report
    assert "7" in report
