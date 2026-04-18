"""Tests for depwatch.cli_filter commands."""
from unittest.mock import patch, MagicMock
from click.testing import CliRunner
from depwatch.cli_filter import filter_cmd
from depwatch.checker import DependencyStatus
from depwatch.config import DepwatchConfig, ProjectConfig


def _s(name, current, latest):
    return DependencyStatus(
        name=name,
        current_version=current,
        latest_version=latest,
        is_outdated=current != latest,
    )


_STATUSES = [
    _s("requests", "2.28.0", "2.31.0"),
    _s("flask", "2.0.0", "2.0.0"),
    _s("django", "3.2.0", "5.0.0"),
]

_CFG = DepwatchConfig(
    projects=[ProjectConfig(name="myapp", requirements_file="requirements.txt")],
    alert=None,
)


@patch("depwatch.cli_filter.check_dependencies", return_value=_STATUSES)
@patch("depwatch.cli_filter.load_config", return_value=_CFG)
def test_outdated_cmd_shows_only_outdated(mock_cfg, mock_check):
    runner = CliRunner()
    result = runner.invoke(filter_cmd, ["outdated"])
    assert result.exit_code == 0
    assert "requests" in result.output
    assert "django" in result.output
    assert "flask" not in result.output


@patch("depwatch.cli_filter.check_dependencies", return_value=_STATUSES)
@patch("depwatch.cli_filter.load_config", return_value=_CFG)
def test_outdated_cmd_ignore(mock_cfg, mock_check):
    runner = CliRunner()
    result = runner.invoke(filter_cmd, ["outdated", "--ignore", "requests"])
    assert result.exit_code == 0
    assert "requests" not in result.output


@patch("depwatch.cli_filter.check_dependencies", return_value=_STATUSES)
@patch("depwatch.cli_filter.load_config", return_value=_CFG)
def test_major_behind_cmd_finds_django(mock_cfg, mock_check):
    runner = CliRunner()
    result = runner.invoke(filter_cmd, ["major-behind", "2"])
    assert result.exit_code == 0
    assert "django" in result.output


@patch("depwatch.cli_filter.check_dependencies", return_value=_STATUSES)
@patch("depwatch.cli_filter.load_config", return_value=_CFG)
def test_major_behind_cmd_no_results(mock_cfg, mock_check):
    runner = CliRunner()
    result = runner.invoke(filter_cmd, ["major-behind", "10"])
    assert result.exit_code == 0
    assert "No dependencies" in result.output
