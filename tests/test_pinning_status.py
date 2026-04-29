"""Tests for depwatch.pinning_status."""
from __future__ import annotations

from depwatch.checker import DependencyStatus
from depwatch.pinning_status import (
    PinningEntry,
    _looks_pinned,
    compute_pinning_status,
    format_pinning_report,
)


def _s(pkg: str, current: str, latest: str, outdated: bool) -> DependencyStatus:
    return DependencyStatus(
        package=pkg,
        current_version=current,
        latest_version=latest,
        is_outdated=outdated,
    )


# ---------------------------------------------------------------------------
# _looks_pinned
# ---------------------------------------------------------------------------

def test_looks_pinned_exact_version():
    assert _looks_pinned("1.2.3") is True


def test_looks_pinned_with_greater_than():
    assert _looks_pinned(">1.0") is False


def test_looks_pinned_with_tilde():
    assert _looks_pinned("~=1.4") is False


def test_looks_pinned_wildcard():
    assert _looks_pinned("1.2.*") is False


def test_looks_pinned_empty_string():
    assert _looks_pinned("") is False


# ---------------------------------------------------------------------------
# compute_pinning_status
# ---------------------------------------------------------------------------

def test_compute_pinning_status_pinned_up_to_date():
    statuses = [_s("requests", "2.31.0", "2.31.0", False)]
    entries = compute_pinning_status("myapp", statuses)
    assert len(entries) == 1
    e = entries[0]
    assert e.is_pinned is True
    assert e.is_outdated is False
    assert e.pin_matches_latest is True


def test_compute_pinning_status_pinned_outdated():
    statuses = [_s("django", "3.2.0", "4.2.0", True)]
    entries = compute_pinning_status("myapp", statuses)
    e = entries[0]
    assert e.is_pinned is True
    assert e.is_outdated is True
    assert e.pin_matches_latest is False


def test_compute_pinning_status_unpinned():
    statuses = [_s("flask", ">=2.0", "3.0.0", True)]
    entries = compute_pinning_status("myapp", statuses)
    e = entries[0]
    assert e.is_pinned is False
    assert e.pin_matches_latest is False


def test_compute_pinning_status_empty():
    assert compute_pinning_status("empty", []) == []


def test_compute_pinning_status_project_name_set():
    statuses = [_s("numpy", "1.24.0", "1.24.0", False)]
    entries = compute_pinning_status("data-project", statuses)
    assert entries[0].project == "data-project"


# ---------------------------------------------------------------------------
# format_pinning_report
# ---------------------------------------------------------------------------

def test_format_pinning_report_no_entries():
    assert format_pinning_report([]) == "No dependencies to report."


def test_format_pinning_report_contains_package_name():
    statuses = [_s("requests", "2.28.0", "2.31.0", True)]
    entries = compute_pinning_status("proj", statuses)
    report = format_pinning_report(entries)
    assert "requests" in report


def test_format_pinning_report_summary_line():
    statuses = [
        _s("requests", "2.31.0", "2.31.0", False),
        _s("flask", ">=2.0", "3.0.0", True),
    ]
    entries = compute_pinning_status("proj", statuses)
    report = format_pinning_report(entries)
    assert "Pinned: 1" in report
    assert "Unpinned: 1" in report
