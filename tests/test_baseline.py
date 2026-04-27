"""Tests for depwatch.baseline."""
import json
from pathlib import Path

import pytest

from depwatch.baseline import save_baseline, load_baseline, diff_from_baseline
from depwatch.checker import DependencyStatus


def _s(pkg: str, current: str, latest: str, outdated: bool) -> DependencyStatus:
    return DependencyStatus(package=pkg, current_version=current, latest_version=latest, outdated=outdated)


@pytest.fixture()
def bf(tmp_path: Path) -> Path:
    return tmp_path / "baseline.json"


def test_save_creates_file(bf):
    statuses = [_s("requests", "2.28.0", "2.31.0", True)]
    save_baseline("proj", statuses, bf)
    assert bf.exists()
    data = json.loads(bf.read_text())
    assert "proj" in data
    assert data["proj"]["packages"][0]["package"] == "requests"


def test_save_multiple_projects(bf):
    save_baseline("proj_a", [_s("flask", "2.0.0", "3.0.0", True)], bf)
    save_baseline("proj_b", [_s("click", "8.0.0", "8.1.0", True)], bf)
    data = json.loads(bf.read_text())
    assert "proj_a" in data and "proj_b" in data


def test_save_overwrites_existing_project(bf):
    """Saving a project twice should replace the previous entry, not duplicate it."""
    save_baseline("proj", [_s("requests", "2.28.0", "2.31.0", True)], bf)
    save_baseline("proj", [_s("flask", "2.0.0", "3.0.0", True)], bf)
    pkgs = load_baseline("proj", bf)
    assert pkgs is not None
    pkg_names = [p["package"] for p in pkgs]
    assert pkg_names == ["flask"]


def test_load_missing_file(bf):
    assert load_baseline("proj", bf) is None


def test_load_missing_project(bf):
    save_baseline("other", [], bf)
    assert load_baseline("proj", bf) is None


def test_load_returns_packages(bf):
    statuses = [_s("numpy", "1.24.0", "1.26.0", True)]
    save_baseline("proj", statuses, bf)
    pkgs = load_baseline("proj", bf)
    assert pkgs is not None and pkgs[0]["package"] == "numpy"


def test_diff_no_baseline(bf):
    current = [_s("requests", "2.28.0", "2.31.0", True)]
    result = diff_from_baseline("proj", current, bf)
    assert result == {"new_outdated": [], "resolved": [], "version_changed": []}


def test_diff_new_outdated(bf):
    save_baseline("proj", [_s("requests", "2.28.0", "2.28.0", False)], bf)
    current = [_s("requests", "2.28.0", "2.31.0", True)]
    result = diff_from_baseline("proj", current, bf)
    assert "requests" in result["new_outdated"]


def test_diff_resolved(bf):
    save_baseline("proj", [_s("flask", "2.0.0", "3.0.0", True)], bf)
    current = [_s("flask", "3.0.0", "3.0.0", False)]
    result = diff_from_baseline("proj", current, bf)
    assert "flask" in result["resolved"]


def test_diff_version_changed(bf):
    save_baseline("proj", [_s("numpy", "1.24.0", "1.25.0", True)], bf)
    current = [_s("numpy", "1.24.0", "1.26.0", True)]
    result = diff_from_baseline("proj", current, bf)
    assert "numpy" in result["version_changed"]
