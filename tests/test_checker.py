"""Tests for depwatch.checker module."""

import pytest
from unittest.mock import patch, MagicMock
from depwatch.checker import (
    get_latest_version,
    check_dependency,
    check_dependencies,
    DependencyStatus,
)


def _mock_pypi_response(version: str) -> MagicMock:
    mock_resp = MagicMock()
    mock_resp.json.return_value = {"info": {"version": version}}
    mock_resp.raise_for_status = MagicMock()
    return mock_resp


@patch("depwatch.checker.requests.get")
def test_get_latest_version(mock_get):
    mock_get.return_value = _mock_pypi_response("2.0.0")
    assert get_latest_version("requests") == "2.0.0"


@patch("depwatch.checker.requests.get")
def test_get_latest_version_network_error(mock_get):
    mock_get.side_effect = Exception("timeout")
    with pytest.raises(RuntimeError, match="Failed to fetch version"):
        get_latest_version("requests")


@patch("depwatch.checker.requests.get")
def test_check_dependency_outdated(mock_get):
    mock_get.return_value = _mock_pypi_response("2.0.0")
    result = check_dependency("requests", "1.0.0")
    assert isinstance(result, DependencyStatus)
    assert result.is_outdated is True
    assert result.latest_version == "2.0.0"
    assert result.error is None


@patch("depwatch.checker.requests.get")
def test_check_dependency_up_to_date(mock_get):
    mock_get.return_value = _mock_pypi_response("2.0.0")
    result = check_dependency("requests", "2.0.0")
    assert result.is_outdated is False


@patch("depwatch.checker.requests.get")
def test_check_dependency_error(mock_get):
    mock_get.side_effect = Exception("network error")
    result = check_dependency("requests", "1.0.0")
    assert result.error is not None
    assert result.latest_version == "unknown"
    assert result.is_outdated is False


@patch("depwatch.checker.requests.get")
def test_check_dependencies_multiple(mock_get):
    mock_get.return_value = _mock_pypi_response("3.0.0")
    deps = {"flask": "2.0.0", "click": "3.0.0"}
    results = check_dependencies(deps)
    assert len(results) == 2
    outdated = [r for r in results if r.is_outdated]
    assert len(outdated) == 1
    assert outdated[0].name == "flask"
