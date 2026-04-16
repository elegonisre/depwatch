"""Tests for depwatch.digest."""
from __future__ import annotations

import json
import os
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from depwatch.digest import build_digest


def _ts(delta_days: int = 0) -> str:
    return (datetime.utcnow() - timedelta(days=delta_days)).isoformat()


def _write_history(path: Path, records: list) -> None:
    with open(path, "w") as fh:
        for rec in records:
            fh.write(json.dumps(rec) + "\n")


@pytest.fixture
def hist(tmp_path):
    p = tmp_path / "hist.jsonl"
    return p


def test_no_data_returns_message(hist):
    hist.write_text("")
    msg = build_digest(str(hist), days=7)
    assert "No data" in msg


def test_digest_includes_run_count(hist):
    records = [
        {"timestamp": _ts(1), "project": "p", "dependencies": []},
        {"timestamp": _ts(2), "project": "p", "dependencies": []},
    ]
    _write_history(hist, records)
    msg = build_digest(str(hist), days=7)
    assert "Runs included : 2" in msg


def test_digest_shows_top_outdated(hist):
    dep_out = {"package": "flask", "current": "1.0", "latest": "2.0", "is_outdated": True}
    dep_ok = {"package": "click", "current": "8.0", "latest": "8.0", "is_outdated": False}
    records = [
        {"timestamp": _ts(0), "project": "p", "dependencies": [dep_out, dep_ok]},
        {"timestamp": _ts(1), "project": "p", "dependencies": [dep_out]},
    ]
    _write_history(hist, records)
    msg = build_digest(str(hist), days=7)
    assert "flask" in msg
    assert "click" not in msg


def test_digest_excludes_old_records(hist):
    records = [
        {"timestamp": _ts(10), "project": "old", "dependencies": []},
    ]
    _write_history(hist, records)
    msg = build_digest(str(hist), days=7)
    assert "No data" in msg


def test_digest_project_breakdown(hist):
    dep_out = {"package": "x", "current": "1", "latest": "2", "is_outdated": True}
    records = [
        {"timestamp": _ts(0), "project": "alpha", "dependencies": [dep_out]},
        {"timestamp": _ts(1), "project": "beta", "dependencies": [dep_out]},
    ]
    _write_history(hist, records)
    msg = build_digest(str(hist), days=7)
    assert "alpha" in msg
    assert "beta" in msg
