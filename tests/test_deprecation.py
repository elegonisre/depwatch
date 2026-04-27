"""Tests for depwatch.deprecation."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from depwatch.checker import DependencyStatus
from depwatch.deprecation import (
    DeprecationEntry,
    _find_successor,
    _is_deprecated,
    check_deprecations,
    format_deprecation_report,
)


def _s(package: str, current: str = "1.0.0", latest: str = "1.0.0") -> DependencyStatus:
    return DependencyStatus(
        package=package,
        current_version=current,
        latest_version=latest,
        is_outdated=current != latest,
    )


def _pypi_info(classifiers=None, description=""):
    return {"info": {"classifiers": classifiers or [], "description": description}}


class TestIsDeprecated:
    def test_inactive_classifier_triggers(self):
        info = _pypi_info(classifiers=["Development Status :: 7 - Inactive"])
        deprecated, reason = _is_deprecated(info)
        assert deprecated is True
        assert reason is not None

    def test_active_classifier_no_trigger(self):
        info = _pypi_info(classifiers=["Development Status :: 5 - Production/Stable"])
        deprecated, _ = _is_deprecated(info)
        assert deprecated is False

    def test_description_deprecated_keyword(self):
        info = _pypi_info(description="This package is deprecated. Use newpkg instead.")
        deprecated, reason = _is_deprecated(info)
        assert deprecated is True
        assert "deprecated" in (reason or "").lower()

    def test_empty_info_returns_false(self):
        deprecated, reason = _is_deprecated({})
        assert deprecated is False
        assert reason is None

    def test_clean_package_not_deprecated(self):
        info = _pypi_info(description="A great utility library.")
        deprecated, _ = _is_deprecated(info)
        assert deprecated is False


class TestFindSuccessor:
    def test_replaced_by_phrase(self):
        info = _pypi_info(description="This is replaced by newlib.")
        assert _find_successor(info) == "newlib"

    def test_no_successor_phrase(self):
        info = _pypi_info(description="Just a normal description.")
        assert _find_successor(info) is None


class TestCheckDeprecations:
    def test_returns_entry_per_status(self):
        statuses = [_s("requests"), _s("flask")]
        with patch("depwatch.deprecation._fetch_pypi_info", return_value={}):
            entries = check_deprecations(statuses, project="myapp")
        assert len(entries) == 2
        assert all(e.project == "myapp" for e in entries)

    def test_deprecated_package_flagged(self):
        statuses = [_s("oldpkg")]
        fake_info = _pypi_info(classifiers=["Development Status :: 7 - Inactive"])
        with patch("depwatch.deprecation._fetch_pypi_info", return_value=fake_info):
            entries = check_deprecations(statuses, project="proj")
        assert entries[0].deprecated is True

    def test_network_error_does_not_raise(self):
        statuses = [_s("somepkg")]
        with patch("depwatch.deprecation._fetch_pypi_info", return_value={}):
            entries = check_deprecations(statuses, project="proj")
        assert entries[0].deprecated is False


class TestFormatDeprecationReport:
    def test_no_deprecated_shows_clean_message(self):
        entries = [
            DeprecationEntry(project="p", package="requests", current_version="2.0", deprecated=False)
        ]
        report = format_deprecation_report(entries)
        assert "No deprecated" in report

    def test_deprecated_entry_appears_in_report(self):
        entries = [
            DeprecationEntry(
                project="p",
                package="oldpkg",
                current_version="1.0",
                deprecated=True,
                reason="Description contains 'deprecated'",
                successor="newpkg",
            )
        ]
        report = format_deprecation_report(entries)
        assert "oldpkg" in report
        assert "newpkg" in report

    def test_summary_counts_correct(self):
        entries = [
            DeprecationEntry(project="p", package="a", current_version="1", deprecated=True),
            DeprecationEntry(project="p", package="b", current_version="1", deprecated=False),
        ]
        report = format_deprecation_report(entries)
        assert "1/2" in report
