"""Tests for depwatch.cli_reachability."""
from __future__ import annotations

import json
from unittest.mock import patch

import pytest
from click.testing import CliRunner

from depwatch.checker import DependencyStatus
from depwatch.cli_reachability import reachability_cmd
from depwatch.config import DepwatchConfig, ProjectConfig
from depwatch.reachability import ReachabilityEntry


def _s(pkg: str, current: str = "1.0.0", latest: str = "2.0.0") -> DependencyStatus:
    return DependencyStatus(
        project_name="proj",
        package_name=pkg,
        current_version=current,
        latest_version=latest,
        is_outdated=current != latest,
    )


def _make_cfg() -> DepwatchConfig:
    return DepwatchConfig(
        projects=[ProjectConfig(name="proj", requirements=["requests==2.28.0"])]
    )


@pytest.fixture()
def runner():
    return CliRunner()


@patch("depwatch.cli_reachability.load_config")
@patch("depwatch.cli_reachability.check_dependencies")
@patch("depwatch.cli_reachability.check_all_reachability")
def test_show_cmd_text(mock_reach, mock_check, mock_cfg, runner):
    mock_cfg.return_value = _make_cfg()
    mock_check.return_value = [_s("requests", "2.28.0", "2.28.0")]
    mock_reach.return_value = [
        ReachabilityEntry(project="proj", package="requests", current_version="2.28.0", yanked=False)
    ]
    result = runner.invoke(reachability_cmd, ["show"])
    assert result.exit_code == 0
    assert "Reachability" in result.output


@patch("depwatch.cli_reachability.load_config")
@patch("depwatch.cli_reachability.check_dependencies")
@patch("depwatch.cli_reachability.check_all_reachability")
def test_show_cmd_json(mock_reach, mock_check, mock_cfg, runner):
    mock_cfg.return_value = _make_cfg()
    mock_check.return_value = [_s("requests")]
    mock_reach.return_value = [
        ReachabilityEntry(project="proj", package="requests", current_version="1.0.0", yanked=True, yanked_reason="bad")
    ]
    result = runner.invoke(reachability_cmd, ["show", "--format", "json"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data[0]["yanked"] is True
    assert data[0]["yanked_reason"] == "bad"


@patch("depwatch.cli_reachability.load_config")
@patch("depwatch.cli_reachability.check_dependencies")
@patch("depwatch.cli_reachability.check_all_reachability")
def test_show_cmd_yanked_only_filter(mock_reach, mock_check, mock_cfg, runner):
    mock_cfg.return_value = _make_cfg()
    mock_check.return_value = [_s("requests"), _s("flask")]
    mock_reach.return_value = [
        ReachabilityEntry(project="proj", package="requests", current_version="1.0.0", yanked=False),
        ReachabilityEntry(project="proj", package="flask", current_version="1.0.0", yanked=True),
    ]
    result = runner.invoke(reachability_cmd, ["show", "--yanked-only", "--format", "json"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert len(data) == 1
    assert data[0]["package"] == "flask"


@patch("depwatch.cli_reachability.load_config", side_effect=FileNotFoundError)
def test_show_cmd_missing_config(mock_cfg, runner):
    result = runner.invoke(reachability_cmd, ["show"])
    assert result.exit_code != 0
    assert "not found" in result.output.lower() or "Error" in result.output
