"""Tests for depwatch.cli_score."""
from unittest.mock import patch, MagicMock
from click.testing import CliRunner
from depwatch.cli_score import score_cmd
from depwatch.checker import DependencyStatus
from depwatch.config import DepwatchConfig, ProjectConfig
import json


def _s(name, outdated):
    return DependencyStatus(
        name=name,
        current_version="1.0",
        latest_version="2.0" if outdated else "1.0",
        outdated=outdated,
    )


def _make_cfg():
    cfg = MagicMock(spec=DepwatchConfig)
    proj = MagicMock(spec=ProjectConfig)
    proj.name = "myapp"
    proj.requirements = ["requests==1.0"]
    cfg.projects = [proj]
    return cfg


@patch("depwatch.cli_score.check_dependencies")
@patch("depwatch.cli_score.load_config")
def test_show_cmd_text(mock_load, mock_check):
    mock_load.return_value = _make_cfg()
    mock_check.return_value = [_s("requests", False)]
    runner = CliRunner()
    result = runner.invoke(score_cmd, ["show"])
    assert result.exit_code == 0
    assert "myapp" in result.output
    assert "100.0%" in result.output


@patch("depwatch.cli_score.check_dependencies")
@patch("depwatch.cli_score.load_config")
def test_show_cmd_json(mock_load, mock_check):
    mock_load.return_value = _make_cfg()
    mock_check.return_value = [_s("requests", False)]
    runner = CliRunner()
    result = runner.invoke(score_cmd, ["show", "--json"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data[0]["project"] == "myapp"
    assert data[0]["score"] == 100.0


@patch("depwatch.cli_score.check_dependencies")
@patch("depwatch.cli_score.load_config")
def test_check_cmd_passes(mock_load, mock_check):
    mock_load.return_value = _make_cfg()
    mock_check.return_value = [_s("requests", False)]
    runner = CliRunner()
    result = runner.invoke(score_cmd, ["check", "--min-score", "80"])
    assert result.exit_code == 0
    assert "meet" in result.output


@patch("depwatch.cli_score.check_dependencies")
@patch("depwatch.cli_score.load_config")
def test_check_cmd_fails(mock_load, mock_check):
    mock_load.return_value = _make_cfg()
    mock_check.return_value = [_s("requests", True), _s("flask", True)]
    runner = CliRunner()
    result = runner.invoke(score_cmd, ["check", "--min-score", "80"])
    assert result.exit_code == 1
    assert "FAIL" in result.output
