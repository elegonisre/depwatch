"""Tests for depwatch.freshness."""
from __future__ import annotations

import json
import math
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from depwatch.freshness import (
    FreshnessEntry,
    _score,
    compute_freshness,
    format_freshness_report,
)


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _ts(delta_days: int = 0) -> str:
    dt = datetime.now(timezone.utc) - timedelta(days=delta_days)
    return dt.isoformat()


def _write_history(path: Path, records: list) -> str:
    fpath = path / "history.json"
    fpath.write_text(json.dumps(records))
    return str(fpath)


@pytest.fixture()
def hist(tmp_path):
    return tmp_path


# ---------------------------------------------------------------------------
# _score
# ---------------------------------------------------------------------------

def test_score_zero_days_is_one():
    assert _score(0) == pytest.approx(1.0, abs=1e-4)


def test_score_none_is_zero():
    assert _score(None) == 0.0


def test_score_decay():
    # At exactly decay days, score should be e^-1 ≈ 0.3679
    assert _score(30, decay=30) == pytest.approx(math.exp(-1), abs=1e-4)


# ---------------------------------------------------------------------------
# compute_freshness
# ---------------------------------------------------------------------------

def test_no_history_returns_empty(hist):
    hp = _write_history(hist, [])
    assert compute_freshness(hp) == []


def test_package_never_up_to_date_has_none_days(hist):
    records = [
        {
            "project": "proj-a",
            "timestamp": _ts(5),
            "statuses": [{"package": "requests", "is_outdated": True}],
        }
    ]
    hp = _write_history(hist, records)
    entries = compute_freshness(hp)
    assert len(entries) == 1
    e = entries[0]
    assert e.days_stale is None
    assert e.freshness_score == 0.0


def test_package_up_to_date_recently_has_high_score(hist):
    records = [
        {
            "project": "proj-a",
            "timestamp": _ts(1),
            "statuses": [{"package": "flask", "is_outdated": False}],
        }
    ]
    hp = _write_history(hist, records)
    entries = compute_freshness(hp)
    assert len(entries) == 1
    assert entries[0].freshness_score > 0.9


def test_project_filter(hist):
    records = [
        {
            "project": "proj-a",
            "timestamp": _ts(0),
            "statuses": [{"package": "numpy", "is_outdated": False}],
        },
        {
            "project": "proj-b",
            "timestamp": _ts(0),
            "statuses": [{"package": "pandas", "is_outdated": False}],
        },
    ]
    hp = _write_history(hist, records)
    entries = compute_freshness(hp, project="proj-a")
    assert all(e.project == "proj-a" for e in entries)
    assert len(entries) == 1


def test_most_recent_ok_timestamp_used(hist):
    """When a package flips back to up-to-date, the latest timestamp wins."""
    records = [
        {
            "project": "p",
            "timestamp": _ts(10),
            "statuses": [{"package": "django", "is_outdated": False}],
        },
        {
            "project": "p",
            "timestamp": _ts(2),
            "statuses": [{"package": "django", "is_outdated": False}],
        },
    ]
    hp = _write_history(hist, records)
    entries = compute_freshness(hp)
    assert entries[0].days_stale is not None
    assert entries[0].days_stale <= 3  # should use the 2-day-old record


# ---------------------------------------------------------------------------
# format_freshness_report
# ---------------------------------------------------------------------------

def test_format_empty():
    assert format_freshness_report([]) == "No freshness data available."


def test_format_contains_package_name(hist):
    records = [
        {
            "project": "myproj",
            "timestamp": _ts(5),
            "statuses": [{"package": "click", "is_outdated": False}],
        }
    ]
    hp = _write_history(hist, records)
    entries = compute_freshness(hp)
    report = format_freshness_report(entries)
    assert "click" in report
    assert "myproj" in report
