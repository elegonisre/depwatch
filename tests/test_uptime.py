"""Tests for depwatch.uptime."""
from __future__ import annotations

import json
import pathlib
from datetime import datetime, timezone

import pytest

from depwatch.uptime import (
    UptimeEntry,
    compute_all_uptime,
    compute_uptime,
    format_uptime_report,
)


@pytest.fixture()
def hist_file(tmp_path: pathlib.Path) -> pathlib.Path:
    return tmp_path / "history.json"


def _write(path: pathlib.Path, records: list) -> None:
    path.write_text(json.dumps(records))


def _rec(project: str, ts: str, is_latest_flags: list[bool]) -> dict:
    return {
        "project": project,
        "timestamp": ts,
        "statuses": [{"package": f"pkg{i}", "is_latest": v} for i, v in enumerate(is_latest_flags)],
    }


# ── compute_uptime ────────────────────────────────────────────────────────────

def test_no_history_returns_none(hist_file):
    _write(hist_file, [])
    assert compute_uptime(str(hist_file), "myproject") is None


def test_all_clean_runs(hist_file):
    _write(hist_file, [
        _rec("proj", "2024-01-01T00:00:00", [True, True]),
        _rec("proj", "2024-01-02T00:00:00", [True, True]),
        _rec("proj", "2024-01-03T00:00:00", [True, True]),
    ])
    e = compute_uptime(str(hist_file), "proj")
    assert e is not None
    assert e.total_runs == 3
    assert e.clean_runs == 3
    assert e.uptime_pct == 100.0
    assert e.current_streak == 3
    assert e.longest_streak == 3


def test_mixed_runs_streak_resets(hist_file):
    _write(hist_file, [
        _rec("proj", "2024-01-01T00:00:00", [True]),
        _rec("proj", "2024-01-02T00:00:00", [False]),  # break
        _rec("proj", "2024-01-03T00:00:00", [True]),
        _rec("proj", "2024-01-04T00:00:00", [True]),
    ])
    e = compute_uptime(str(hist_file), "proj")
    assert e.clean_runs == 3
    assert e.uptime_pct == 75.0
    assert e.current_streak == 2
    assert e.longest_streak == 2


def test_last_clean_is_set(hist_file):
    _write(hist_file, [
        _rec("proj", "2024-03-15T12:00:00", [True]),
    ])
    e = compute_uptime(str(hist_file), "proj")
    assert e.last_clean == datetime(2024, 3, 15, 12, 0, 0, tzinfo=timezone.utc)


def test_compute_all_uptime_multiple_projects(hist_file):
    _write(hist_file, [
        _rec("alpha", "2024-01-01T00:00:00", [True]),
        _rec("beta", "2024-01-01T00:00:00", [False]),
        _rec("alpha", "2024-01-02T00:00:00", [True]),
    ])
    entries = compute_all_uptime(str(hist_file))
    names = {e.project for e in entries}
    assert names == {"alpha", "beta"}
    alpha = next(e for e in entries if e.project == "alpha")
    assert alpha.clean_runs == 2


# ── format_uptime_report ──────────────────────────────────────────────────────

def test_format_empty_returns_message():
    assert "No uptime" in format_uptime_report([])


def test_format_contains_project_name(hist_file):
    _write(hist_file, [_rec("myproject", "2024-01-01T00:00:00", [True])])
    entries = compute_all_uptime(str(hist_file))
    report = format_uptime_report(entries)
    assert "myproject" in report
    assert "100.0" in report
