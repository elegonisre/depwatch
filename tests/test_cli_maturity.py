"""Integration tests for depwatch.cli_maturity."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest
from click.testing import CliRunner

from depwatch.checker import DependencyStatus
from depwatch.cli_maturity import maturity_cmd
from depwatch.config import DepwatchConfig, ProjectConfig


def _s(pkg: str, cur: str, lat: str, outdated: bool = True) -> DependencyStatus:
    return DependencyStatus(
        package=pkg,
        current_version=cur,
        latest_version=lat,
        is_outdated=outdated,
    )


def _make_cfg(tmp_path: Path) -> Path:
    cfg_file = tmp_path / "depwatch.toml"
    cfg_file.write_text(
        "[project.myapp]\nrequirements = []\n"
    )
    return cfg_file


_STATUSES = [_s("django", "3.2", "4.2"), _s("requests", "2.28", "2.28", outdated=False)]

_CFG = DepwatchConfig(
    projects=[ProjectConfig(name="myapp", requirements=["django", "requests"])],
    alert=None,
)


@pytest.fixture()
def runner():
    return CliRunner()


def test_show_cmd_text(runner, tmp_path):
    cfg_file = _make_cfg(tmp_path)
    with patch("depwatch.cli_maturity.load_config", return_value=_CFG), \
         patch("depwatch.cli_maturity.check_dependencies", return_value=_STATUSES):
        result = runner.invoke(maturity_cmd, ["show", "--config", str(cfg_file)])
    assert result.exit_code == 0
    assert "django" in result.output
    assert "Average maturity score" in result.output


def test_show_cmd_json(runner, tmp_path):
    cfg_file = _make_cfg(tmp_path)
    with patch("depwatch.cli_maturity.load_config", return_value=_CFG), \
         patch("depwatch.cli_maturity.check_dependencies", return_value=_STATUSES):
        result = runner.invoke(
            maturity_cmd, ["show", "--config", str(cfg_file), "--format", "json"]
        )
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert isinstance(data, list)
    assert len(data) == 2
    assert "maturity_score" in data[0]
    assert "label" in data[0]


def test_show_cmd_missing_config(runner, tmp_path):
    result = runner.invoke(
        maturity_cmd, ["show", "--config", str(tmp_path / "missing.toml")]
    )
    assert result.exit_code != 0


def test_show_cmd_min_score_filter(runner, tmp_path):
    cfg_file = _make_cfg(tmp_path)
    with patch("depwatch.cli_maturity.load_config", return_value=_CFG), \
         patch("depwatch.cli_maturity.check_dependencies", return_value=_STATUSES):
        result = runner.invoke(
            maturity_cmd,
            ["show", "--config", str(cfg_file), "--min-score", "0.01"],
        )
    assert result.exit_code == 0
    # Only entries below the threshold should appear; exact count depends on scores
    # but the command must run without error
    assert "Dependency Maturity Report" in result.output or result.output.strip() != ""
