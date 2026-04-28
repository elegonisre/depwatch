"""Tests for depwatch.reachability."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from depwatch.checker import DependencyStatus
from depwatch.reachability import (
    ReachabilityEntry,
    check_reachability,
    check_all_reachability,
    format_reachability_report,
)


def _s(package: str, current: str = "1.0.0", latest: str = "2.0.0") -> DependencyStatus:
    return DependencyStatus(
        project_name="myproject",
        package_name=package,
        current_version=current,
        latest_version=latest,
        is_outdated=current != latest,
    )


def _pypi_response(yanked: bool = False, yanked_reason: str | None = None) -> dict:
    return {
        "info": {"yanked": yanked, "yanked_reason": yanked_reason},
        "urls": [
            {"yanked": yanked, "yanked_reason": yanked_reason, "filename": "pkg.whl"}
        ],
    }


@patch("depwatch.reachability._fetch_version_info")
def test_check_reachability_not_yanked(mock_fetch):
    mock_fetch.return_value = _pypi_response(yanked=False)
    entry = check_reachability(_s("requests", "2.28.0"))
    assert entry.yanked is False
    assert entry.yanked_reason is None
    assert entry.error is None


@patch("depwatch.reachability._fetch_version_info")
def test_check_reachability_yanked(mock_fetch):
    mock_fetch.return_value = _pypi_response(yanked=True, yanked_reason="Security issue")
    entry = check_reachability(_s("badpkg", "0.1.0"))
    assert entry.yanked is True
    assert entry.yanked_reason == "Security issue"
    assert entry.error is None


@patch("depwatch.reachability._fetch_version_info")
def test_check_reachability_network_error(mock_fetch):
    mock_fetch.side_effect = ConnectionError("timeout")
    entry = check_reachability(_s("flaky", "1.0.0"))
    assert entry.yanked is False
    assert "timeout" in (entry.error or "")


@patch("depwatch.reachability._fetch_version_info")
def test_check_all_reachability_returns_one_per_status(mock_fetch):
    mock_fetch.return_value = _pypi_response()
    statuses = [_s("pkg-a"), _s("pkg-b"), _s("pkg-c")]
    entries = check_all_reachability(statuses)
    assert len(entries) == 3
    assert {e.package for e in entries} == {"pkg-a", "pkg-b", "pkg-c"}


def test_format_reachability_report_all_clean():
    entries = [
        ReachabilityEntry(project="p", package="a", current_version="1.0", yanked=False)
    ]
    report = format_reachability_report(entries)
    assert "All checked versions are reachable" in report


def test_format_reachability_report_shows_yanked():
    entries = [
        ReachabilityEntry(
            project="p", package="evil", current_version="0.9",
            yanked=True, yanked_reason="CVE-2024-1234"
        )
    ]
    report = format_reachability_report(entries)
    assert "evil" in report
    assert "CVE-2024-1234" in report
    assert "Yanked packages" in report


def test_format_reachability_report_shows_errors():
    entries = [
        ReachabilityEntry(
            project="p", package="broken", current_version="1.0",
            yanked=False, error="HTTP 404"
        )
    ]
    report = format_reachability_report(entries)
    assert "broken" in report
    assert "HTTP 404" in report
    assert "Check errors" in report
