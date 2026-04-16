"""Tests for depwatch.snapshot diff logic."""
import pytest
from depwatch.checker import DependencyStatus
from depwatch.snapshot import diff_snapshots, SnapshotDiff


def _s(package: str, current: str, latest: str, outdated: bool) -> DependencyStatus:
    return DependencyStatus(package=package, current_version=current, latest_version=latest, outdated=outdated)


def test_new_outdated_detected():
    previous = [_s("requests", "2.28.0", "2.28.0", False)]
    current = [_s("requests", "2.28.0", "2.31.0", True)]
    diff = diff_snapshots("myapp", previous, current)
    assert len(diff.new_outdated) == 1
    assert diff.new_outdated[0].package == "requests"
    assert diff.has_changes


def test_resolved_detected():
    previous = [_s("flask", "2.0.0", "3.0.0", True)]
    current = [_s("flask", "3.0.0", "3.0.0", False)]
    diff = diff_snapshots("myapp", previous, current)
    assert len(diff.resolved) == 1
    assert diff.resolved[0].package == "flask"
    assert diff.has_changes


def test_changed_version_while_still_outdated():
    previous = [_s("numpy", "1.21.0", "1.25.0", True)]
    current = [_s("numpy", "1.23.0", "1.25.0", True)]
    diff = diff_snapshots("myapp", previous, current)
    assert len(diff.changed_version) == 1
    assert diff.changed_version[0].old_version == "1.21.0"
    assert diff.changed_version[0].new_version == "1.23.0"


def test_unchanged_up_to_date():
    previous = [_s("click", "8.1.0", "8.1.0", False)]
    current = [_s("click", "8.1.0", "8.1.0", False)]
    diff = diff_snapshots("myapp", previous, current)
    assert len(diff.unchanged) == 1
    assert not diff.has_changes


def test_new_package_outdated_no_previous():
    previous: list = []
    current = [_s("boto3", "1.20.0", "1.34.0", True)]
    diff = diff_snapshots("myapp", previous, current)
    assert len(diff.new_outdated) == 1
    assert diff.new_outdated[0].old_status is None


def test_multiple_packages_mixed():
    previous = [
        _s("requests", "2.28.0", "2.28.0", False),
        _s("flask", "2.0.0", "3.0.0", True),
    ]
    current = [
        _s("requests", "2.28.0", "2.31.0", True),
        _s("flask", "3.0.0", "3.0.0", False),
    ]
    diff = diff_snapshots("myapp", previous, current)
    assert len(diff.new_outdated) == 1
    assert len(diff.resolved) == 1
    assert diff.has_changes


def test_project_name_preserved():
    diff = diff_snapshots("coolproject", [], [])
    assert diff.project == "coolproject"
