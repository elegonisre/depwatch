"""Tests for depwatch.cli_pinning_status."""
from __future__ import annotations

import json
from unittest.mock import patch, MagicMock

from click.testing import CliRunner

from depwatch.checker import DependencyStatus
from depwatch.cli_pinning_status import pinning_cmd
from depwatch.config import DepwatchConfig, ProjectConfig


def _s(pkg: str, current: str, latest: str, outdated: bool) -> DependencyStatus:
    return DependencyStatus(
        package=pkg,
        current_version=current,
        latest_version=latest,
        is_outdated=outdated,
    )


def _make_cfg(name: str = "myapp") -> DepwatchConfig:
    return DepwatchConfig(
        projects=[ProjectConfig(name=name, requirements=["requirements.txt"])],
        alert=None,
    )


runner = CliRunner()


@patch("depwatch.cli_pinning_status.check_dependencies")
@patch("depwatch.cli_pinning_status.load_config")
def test_show_cmd_text(mock_cfg, mock_check):
    mock_cfg.return_value = _make_cfg()
    mock_check.return_value = [
        _s("requests", "2.31.0", "2.31.0", False),
        _s("django", "3.2.0", "4.2.0", True),
    ]
    result = runner.invoke(pinning_cmd, ["show"])
    assert result.exit_code == 0
    assert "requests" in result.output
    assert "django" in result.output


@patch("depwatch.cli_pinning_status.check_dependencies")
@patch("depwatch.cli_pinning_status.load_config")
def test_show_cmd_json(mock_cfg, mock_check):
    mock_cfg.return_value = _make_cfg()
    mock_check.return_value = [_s("flask", "2.3.0", "3.0.0", True)]
    result = runner.invoke(pinning_cmd, ["show", "--format", "json"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert isinstance(data, list)
    assert data[0]["package"] == "flask"
    assert data[0]["is_outdated"] is True


@patch("depwatch.cli_pinning_status.check_dependencies")
@patch("depwatch.cli_pinning_status.load_config")
def test_show_cmd_unpinned_only(mock_cfg, mock_check):
    mock_cfg.return_value = _make_cfg()
    mock_check.return_value = [
        _s("requests", "2.31.0", "2.31.0", False),   # pinned
        _s("flask", ">=2.0", "3.0.0", True),          # unpinned
    ]
    result = runner.invoke(pinning_cmd, ["show", "--unpinned-only"])
    assert result.exit_code == 0
    assert "flask" in result.output
    assert "requests" not in result.output


@patch("depwatch.cli_pinning_status.load_config")
def test_show_cmd_missing_config(mock_cfg):
    mock_cfg.side_effect = FileNotFoundError
    result = runner.invoke(pinning_cmd, ["show", "--config", "missing.toml"])
    assert result.exit_code != 0
    assert "not found" in result.output


@patch("depwatch.cli_pinning_status.check_dependencies")
@patch("depwatch.cli_pinning_status.load_config")
def test_show_cmd_project_filter(mock_cfg, mock_check):
    cfg = DepwatchConfig(
        projects=[
            ProjectConfig(name="alpha", requirements=["r.txt"]),
            ProjectConfig(name="beta", requirements=["r.txt"]),
        ],
        alert=None,
    )
    mock_cfg.return_value = cfg
    mock_check.return_value = [_s("numpy", "1.24.0", "1.24.0", False)]
    result = runner.invoke(pinning_cmd, ["show", "--project", "alpha"])
    assert result.exit_code == 0
    # check_dependencies called once (only alpha)
    assert mock_check.call_count == 1
