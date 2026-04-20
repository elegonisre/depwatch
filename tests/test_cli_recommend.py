"""Tests for depwatch.cli_recommend."""
from __future__ import annotations

from unittest.mock import patch, MagicMock

import json
import pytest
from click.testing import CliRunner

from depwatch.checker import DependencyStatus
from depwatch.cli_recommend import recommend_cmd
from depwatch.config import ProjectConfig, DepwatchConfig


def _s(pkg, current, latest, project="myproject"):
    return DependencyStatus(
        project=project,
        package=pkg,
        current_version=current,
        latest_version=latest,
        is_up_to_date=(current == latest),
    )


def _make_cfg():
    proj = ProjectConfig(name="myproject", requirements=["django"])
    return DepwatchConfig(projects=[proj])


@patch("depwatch.cli_recommend.load_config", return_value=_make_cfg())
@patch(
    "depwatch.cli_recommend.check_dependencies",
    return_value=[_s("django", "3.0.0", "4.2.0")],
)
@patch(
    "depwatch.cli_recommend.build_recommendations",
    return_value=[
        MagicMock(
            project="myproject",
            package="django",
            current_version="3.0.0",
            latest_version="4.2.0",
            risk_label="high",
            priority=2,
            reason="Upgrade django from 3.0.0 to 4.2.0; 1 major version(s) behind",
        )
    ],
)
def test_show_cmd_text(mock_recs, mock_check, mock_cfg):
    runner = CliRunner()
    result = runner.invoke(recommend_cmd, ["show"])
    assert result.exit_code == 0
    assert "django" in result.output


@patch("depwatch.cli_recommend.load_config", return_value=_make_cfg())
@patch(
    "depwatch.cli_recommend.check_dependencies",
    return_value=[_s("django", "3.0.0", "4.2.0")],
)
@patch(
    "depwatch.cli_recommend.build_recommendations",
    return_value=[
        MagicMock(
            project="myproject",
            package="django",
            current_version="3.0.0",
            latest_version="4.2.0",
            risk_label="high",
            priority=2,
            reason="Upgrade django from 3.0.0 to 4.2.0",
        )
    ],
)
def test_show_cmd_json(mock_recs, mock_check, mock_cfg):
    runner = CliRunner()
    result = runner.invoke(recommend_cmd, ["show", "--format", "json"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert isinstance(data, list)
    assert data[0]["package"] == "django"


@patch("depwatch.cli_recommend.load_config", side_effect=FileNotFoundError)
def test_show_cmd_missing_config(mock_cfg):
    runner = CliRunner()
    result = runner.invoke(recommend_cmd, ["show"])
    assert result.exit_code != 0


@patch("depwatch.cli_recommend.load_config", return_value=_make_cfg())
@patch("depwatch.cli_recommend.check_dependencies", return_value=[])
@patch("depwatch.cli_recommend.build_recommendations", return_value=[])
def test_show_cmd_no_recs(mock_recs, mock_check, mock_cfg):
    runner = CliRunner()
    result = runner.invoke(recommend_cmd, ["show"])
    assert result.exit_code == 0
    assert "up to date" in result.output.lower()
