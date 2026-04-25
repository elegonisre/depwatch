"""Tests for depwatch.dependency_age."""
from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import patch, MagicMock

import pytest

from depwatch.checker import DependencyStatus
from depwatch.dependency_age import (
    DependencyAge,
    _fetch_release_date,
    compute_dependency_ages,
    format_age_table,
)


def _s(pkg, installed, latest, outdated=True) -> DependencyStatus:
    return DependencyStatus(
        package=pkg,
        installed_version=installed,
        latest_version=latest,
        is_outdated=outdated,
    )


def _pypi_response(date_str: str) -> MagicMock:
    mock = MagicMock()
    mock.raise_for_status.return_value = None
    mock.json.return_value = {"urls": [{"upload_time_iso_8601": date_str}]}
    return mock


def test_fetch_release_date_success():
    with patch("depwatch.dependency_age.requests.get") as mock_get:
        mock_get.return_value = _pypi_response("2023-06-15T12:00:00Z")
        dt = _fetch_release_date("requests", "2.28.0")
    assert dt is not None
    assert dt.year == 2023
    assert dt.tzinfo is not None


def test_fetch_release_date_network_error():
    with patch("depwatch.dependency_age.requests.get", side_effect=Exception("timeout")):
        dt = _fetch_release_date("requests", "2.28.0")
    assert dt is None


def test_fetch_release_date_no_urls():
    mock = MagicMock()
    mock.raise_for_status.return_value = None
    mock.json.return_value = {"urls": []}
    with patch("depwatch.dependency_age.requests.get", return_value=mock):
        dt = _fetch_release_date("requests", "2.28.0")
    assert dt is None


def test_compute_dependency_ages_calculates_days_behind():
    installed_dt = datetime(2022, 1, 1, tzinfo=timezone.utc)
    latest_dt = datetime(2023, 1, 1, tzinfo=timezone.utc)

    with patch("depwatch.dependency_age._fetch_release_date") as mock_fetch:
        mock_fetch.side_effect = [installed_dt, latest_dt]
        result = compute_dependency_ages("myproject", [_s("django", "3.2", "4.0")])

    assert len(result) == 1
    entry = result[0]
    assert entry.package == "django"
    assert entry.days_behind == 365
    assert entry.is_outdated is True


def test_compute_dependency_ages_up_to_date():
    same_dt = datetime(2023, 6, 1, tzinfo=timezone.utc)

    with patch("depwatch.dependency_age._fetch_release_date", return_value=same_dt):
        result = compute_dependency_ages("proj", [_s("flask", "2.3", "2.3", outdated=False)])

    assert result[0].days_behind == 0


def test_format_age_table_empty():
    assert "No dependency" in format_age_table([])


def test_format_age_table_sorted_by_days_behind():
    entries = [
        DependencyAge("p", "a", "1.0", "2.0", None, None, 10, True),
        DependencyAge("p", "b", "1.0", "3.0", None, None, 500, True),
        DependencyAge("p", "c", "1.0", "1.1", None, None, 2, False),
    ]
    table = format_age_table(entries)
    assert table.index("b") < table.index("a") < table.index("c")
