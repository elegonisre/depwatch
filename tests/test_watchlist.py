"""Tests for depwatch.watchlist."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from depwatch.checker import DependencyStatus
from depwatch.watchlist import (
    add_to_watchlist,
    filter_watchlist,
    format_watchlist_report,
    load_watchlist,
    remove_from_watchlist,
    save_watchlist,
)


@pytest.fixture()
def wl_file(tmp_path: Path) -> Path:
    return tmp_path / "watchlist.json"


def _s(pkg: str, current: str, latest: str) -> DependencyStatus:
    return DependencyStatus(
        package=pkg,
        current_version=current,
        latest_version=latest,
        is_outdated=current != latest,
    )


def test_load_missing_file_returns_empty(wl_file: Path) -> None:
    assert load_watchlist(wl_file) == []


def test_save_and_load_roundtrip(wl_file: Path) -> None:
    save_watchlist(["requests", "flask"], wl_file)
    assert load_watchlist(wl_file) == ["flask", "requests"]


def test_add_new_package(wl_file: Path) -> None:
    result = add_to_watchlist("django", wl_file)
    assert "django" in result
    assert load_watchlist(wl_file) == ["django"]


def test_add_duplicate_is_idempotent(wl_file: Path) -> None:
    add_to_watchlist("django", wl_file)
    add_to_watchlist("django", wl_file)
    assert load_watchlist(wl_file).count("django") == 1


def test_remove_existing_package(wl_file: Path) -> None:
    save_watchlist(["requests", "flask"], wl_file)
    result = remove_from_watchlist("flask", wl_file)
    assert "flask" not in result
    assert "requests" in result


def test_remove_missing_package_is_noop(wl_file: Path) -> None:
    save_watchlist(["requests"], wl_file)
    result = remove_from_watchlist("nonexistent", wl_file)
    assert result == ["requests"]


def test_filter_watchlist_returns_matching(wl_file: Path) -> None:
    save_watchlist(["requests"], wl_file)
    statuses = [_s("requests", "2.28.0", "2.31.0"), _s("flask", "2.0.0", "2.0.0")]
    result = filter_watchlist(statuses, wl_file)
    assert len(result) == 1
    assert result[0].package == "requests"


def test_filter_watchlist_empty_watchlist(wl_file: Path) -> None:
    statuses = [_s("requests", "2.28.0", "2.31.0")]
    assert filter_watchlist(statuses, wl_file) == []


def test_format_watchlist_report_outdated() -> None:
    statuses = [_s("requests", "2.28.0", "2.31.0")]
    report = format_watchlist_report(statuses)
    assert "[OUTDATED]" in report
    assert "requests" in report


def test_format_watchlist_report_empty() -> None:
    report = format_watchlist_report([])
    assert "No watchlisted" in report
