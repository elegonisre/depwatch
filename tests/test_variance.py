"""Tests for depwatch.variance."""
from __future__ import annotations

import json
import pathlib

import pytest

from depwatch.variance import (
    VarianceEntry,
    _stability_label,
    compute_all_variance,
    compute_variance,
    format_variance_report,
)


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _rec(project: str, pkg: str, installed: str, latest: str, ts: str = "2024-01-01T00:00:00") -> dict:
    return {
        "project": project,
        "package": pkg,
        "installed_version": installed,
        "latest_version": latest,
        "timestamp": ts,
    }


@pytest.fixture()
def hist(tmp_path: pathlib.Path):
    """Return a factory that writes a history JSON file and returns its path."""
    p = tmp_path / "history.json"

    def _write(records: list) -> str:
        p.write_text(json.dumps(records))
        return str(p)

    return _write


# ---------------------------------------------------------------------------
# unit tests
# ---------------------------------------------------------------------------

def test_stability_label_stable():
    assert _stability_label(0.5) == "stable"


def test_stability_label_moderate():
    assert _stability_label(2.0) == "moderate"


def test_stability_label_volatile():
    assert _stability_label(4.0) == "volatile"


def test_no_history_returns_none(hist):
    path = hist([])
    assert compute_variance(path, "myproject") is None


def test_single_run_zero_variance(hist):
    records = [
        _rec("proj", "requests", "2.0", "2.1", "2024-01-01T00:00:00"),
        _rec("proj", "flask", "1.0", "1.0", "2024-01-01T00:00:00"),
    ]
    path = hist(records)
    entry = compute_variance(path, "proj")
    assert entry is not None
    assert entry.run_count == 1
    assert entry.variance == 0.0
    assert entry.std_dev == 0.0
    assert entry.mean_outdated == 1.0
    assert entry.stability_label == "stable"


def test_two_runs_computes_variance(hist):
    records = [
        _rec("proj", "requests", "2.0", "2.1", "2024-01-01T00:00:00"),  # outdated
        _rec("proj", "flask", "1.0", "1.0", "2024-01-01T00:00:00"),  # up to date
        _rec("proj", "requests", "2.1", "2.1", "2024-01-02T00:00:00"),  # now up to date
        _rec("proj", "flask", "1.0", "2.0", "2024-01-02T00:00:00"),  # now outdated
    ]
    path = hist(records)
    entry = compute_variance(path, "proj")
    assert entry is not None
    assert entry.run_count == 2
    assert entry.mean_outdated == 1.0
    assert entry.min_outdated == 1
    assert entry.max_outdated == 1


def test_compute_all_variance_multiple_projects(hist):
    records = [
        _rec("alpha", "requests", "1.0", "2.0", "2024-01-01T00:00:00"),
        _rec("beta", "django", "3.0", "4.0", "2024-01-01T00:00:00"),
    ]
    path = hist(records)
    entries = compute_all_variance(path)
    names = {e.project for e in entries}
    assert "alpha" in names
    assert "beta" in names


def test_format_variance_report_no_entries():
    assert format_variance_report([]) == "No variance data available."


def test_format_variance_report_contains_project(hist):
    records = [_rec("myproj", "requests", "1.0", "2.0", "2024-01-01T00:00:00")]
    path = hist(records)
    entry = compute_variance(path, "myproj")
    report = format_variance_report([entry])
    assert "myproj" in report
    assert "stable" in report or "moderate" in report or "volatile" in report
