"""Tests for depwatch.velocity."""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from depwatch.velocity import VelocityEntry, compute_velocity, format_velocity_report


def _ts(days_ago: float) -> str:
    dt = datetime.now(timezone.utc) - timedelta(days=days_ago)
    return dt.isoformat()


def _write_history(path: Path, records: list[dict]) -> None:
    path.write_text(json.dumps(records))


@pytest.fixture()
def hist(tmp_path: Path) -> Path:
    return tmp_path / "history.json"


def _rec(project: str, days_ago: float, outdated_count: int) -> dict:
    statuses = [
        {"name": f"pkg{i}", "is_latest": False} for i in range(outdated_count)
    ]
    return {"project": project, "timestamp": _ts(days_ago), "statuses": statuses}


# ── fewer than 2 runs returns None ──────────────────────────────────────────

def test_no_history_returns_none(hist: Path) -> None:
    _write_history(hist, [])
    result = compute_velocity(str(hist), "myproject")
    assert result is None


def test_single_run_returns_none(hist: Path) -> None:
    _write_history(hist, [_rec("myproject", 5, 3)])
    result = compute_velocity(str(hist), "myproject")
    assert result is None


# ── basic velocity calculation ───────────────────────────────────────────────

def test_velocity_positive(hist: Path) -> None:
    _write_history(hist, [
        _rec("myproject", 10, 2),
        _rec("myproject", 0, 6),
    ])
    entry = compute_velocity(str(hist), "myproject", window_days=30)
    assert isinstance(entry, VelocityEntry)
    assert entry.total_outdated_delta == 4
    assert entry.outdated_per_day > 0


def test_velocity_negative(hist: Path) -> None:
    _write_history(hist, [
        _rec("myproject", 10, 8),
        _rec("myproject", 0, 2),
    ])
    entry = compute_velocity(str(hist), "myproject")
    assert entry is not None
    assert entry.total_outdated_delta == -6
    assert entry.outdated_per_day < 0


def test_window_excludes_old_runs(hist: Path) -> None:
    _write_history(hist, [
        _rec("myproject", 60, 1),  # outside 30-day window
        _rec("myproject", 5, 3),
        _rec("myproject", 0, 5),
    ])
    entry = compute_velocity(str(hist), "myproject", window_days=30)
    assert entry is not None
    # Only the two recent runs should be used
    assert entry.total_outdated_delta == 2


def test_project_isolation(hist: Path) -> None:
    _write_history(hist, [
        _rec("alpha", 10, 1),
        _rec("alpha", 0, 5),
        _rec("beta", 10, 0),
        _rec("beta", 0, 0),
    ])
    alpha = compute_velocity(str(hist), "alpha")
    beta = compute_velocity(str(hist), "beta")
    assert alpha is not None and alpha.total_outdated_delta == 4
    assert beta is not None and beta.total_outdated_delta == 0


# ── format_velocity_report ───────────────────────────────────────────────────

def test_format_empty_returns_message() -> None:
    out = format_velocity_report([])
    assert "No velocity data" in out


def test_format_shows_project_name(hist: Path) -> None:
    _write_history(hist, [
        _rec("coolapp", 7, 1),
        _rec("coolapp", 0, 4),
    ])
    entry = compute_velocity(str(hist), "coolapp")
    assert entry is not None
    report = format_velocity_report([entry])
    assert "coolapp" in report
    assert "outdated/day" in report
