"""Tests for depwatch.cadence."""
import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from depwatch.cadence import (
    CadenceEntry,
    _regularity_label,
    compute_cadence,
    format_cadence_report,
)


def _ts(dt: str) -> str:
    return dt


def _write_history(path: Path, records: list) -> None:
    path.write_text(json.dumps(records))


@pytest.fixture
def hist(tmp_path):
    return tmp_path / "history.json"


def test_no_history_returns_empty(hist):
    _write_history(hist, [])
    assert compute_cadence(str(hist)) == []


def test_regularity_label_very_frequent():
    assert _regularity_label(0.5) == "very frequent"


def test_regularity_label_frequent():
    assert _regularity_label(6) == "frequent"


def test_regularity_label_regular():
    assert _regularity_label(24) == "regular"


def test_regularity_label_infrequent():
    assert _regularity_label(100) == "infrequent"


def test_regularity_label_rare():
    assert _regularity_label(200) == "rare"


def test_regularity_label_none():
    assert _regularity_label(None) == "unknown"


def test_single_run_no_avg_interval(hist):
    records = [
        {"project": "myapp", "timestamp": "2024-01-01T10:00:00", "statuses": []}
    ]
    _write_history(hist, records)
    entries = compute_cadence(str(hist))
    assert len(entries) == 1
    e = entries[0]
    assert e.project == "myapp"
    assert e.run_count == 1
    assert e.avg_interval_hours is None
    assert e.regularity_label == "unknown"


def test_two_runs_computes_avg(hist):
    records = [
        {"project": "myapp", "timestamp": "2024-01-01T10:00:00", "statuses": []},
        {"project": "myapp", "timestamp": "2024-01-01T22:00:00", "statuses": []},
    ]
    _write_history(hist, records)
    entries = compute_cadence(str(hist))
    assert len(entries) == 1
    assert entries[0].avg_interval_hours == pytest.approx(12.0)
    assert entries[0].regularity_label == "frequent"


def test_multiple_projects_sorted(hist):
    records = [
        {"project": "beta", "timestamp": "2024-01-01T00:00:00", "statuses": []},
        {"project": "alpha", "timestamp": "2024-01-01T00:00:00", "statuses": []},
    ]
    _write_history(hist, records)
    entries = compute_cadence(str(hist))
    assert [e.project for e in entries] == ["alpha", "beta"]


def test_format_report_contains_project(hist):
    records = [
        {"project": "webapp", "timestamp": "2024-03-01T08:00:00", "statuses": []},
        {"project": "webapp", "timestamp": "2024-03-02T08:00:00", "statuses": []},
    ]
    _write_history(hist, records)
    entries = compute_cadence(str(hist))
    report = format_cadence_report(entries)
    assert "webapp" in report
    assert "2 runs" in report


def test_format_report_empty():
    assert format_cadence_report([]) == "No cadence data available."
