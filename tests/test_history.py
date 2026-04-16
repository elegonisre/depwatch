"""Tests for depwatch.history persistence module."""

import json
import os
import pytest

from depwatch.checker import DependencyStatus
from depwatch.history import (
    save_run,
    load_history,
    get_project_history,
    clear_history,
)


@pytest.fixture()
def hist_file(tmp_path):
    return str(tmp_path / "history.json")


def _make_status(package, current, latest, outdated):
    return DependencyStatus(
        package=package,
        current_version=current,
        latest_version=latest,
        outdated=outdated,
    )


def test_load_history_missing_file(hist_file):
    assert load_history(hist_file) == []


def test_save_and_load(hist_file):
    statuses = [_make_status("requests", "2.28.0", "2.31.0", True)]
    save_run("proj_a", statuses, hist_file)
    records = load_history(hist_file)
    assert len(records) == 1
    assert records[0]["package"] == "requests"
    assert records[0]["project"] == "proj_a"
    assert records[0]["outdated"] is True


def test_save_appends_across_runs(hist_file):
    s1 = [_make_status("flask", "2.0.0", "2.3.0", True)]
    s2 = [_make_status("flask", "2.3.0", "2.3.0", False)]
    save_run("proj_a", s1, hist_file)
    save_run("proj_a", s2, hist_file)
    records = load_history(hist_file)
    assert len(records) == 2


def test_get_project_history_filters(hist_file):
    save_run("proj_a", [_make_status("flask", "2.0", "2.3", True)], hist_file)
    save_run("proj_b", [_make_status("django", "4.0", "4.2", True)], hist_file)
    proj_a_records = get_project_history("proj_a", hist_file)
    assert all(r["project"] == "proj_a" for r in proj_a_records)
    assert len(proj_a_records) == 1


def test_clear_history(hist_file):
    save_run("proj_a", [_make_status("flask", "2.0", "2.3", True)], hist_file)
    clear_history(hist_file)
    assert not os.path.exists(hist_file)


def test_clear_history_no_file(hist_file):
    # Should not raise
    clear_history(hist_file)


def test_checked_at_is_iso_format(hist_file):
    from datetime import datetime
    save_run("proj_a", [_make_status("click", "8.0", "8.1", True)], hist_file)
    record = load_history(hist_file)[0]
    # Should parse without error
    datetime.fromisoformat(record["checked_at"])
