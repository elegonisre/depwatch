"""Tests for depwatch.cli_threshold."""
from __future__ import annotations

from unittest.mock import patch

import pytest
from click.testing import CliRunner

from depwatch.checker import DependencyStatus
from depwatch.cli_threshold import threshold_cmd
from depwatch.config import DepwatchConfig, ProjectConfig


def _s(name: str, outdated: bool) -> DependencyStatus:
    return DependencyStatus(
        name=name,
        current_version="1.0.0",
        latest_version="2.0.0" if outdated else "1.0.0",
        is_outdated=outdated,
    )


def _make_cfg(req: list[str] | None = None) -> DepwatchConfig:
    return DepwatchConfig(
        projects=[ProjectConfig(name="myproject", requirements=req or ["requests"])]
    )


runner = CliRunner()


def test_check_cmd_passes_when_under_threshold():
    statuses = [_s("requests", False)]
    with patch("depwatch.cli_threshold.load_config", return_value=_make_cfg()), \
         patch("depwatch.cli_threshold.check_dependencies", return_value=statuses):
        result = runner.invoke(threshold_cmd, ["check", "--max-outdated", "1"])
    assert result.exit_code == 0
    assert "[OK]" in result.output


def test_check_cmd_fails_when_over_threshold():
    statuses = [_s("requests", True), _s("flask", True)]
    with patch("depwatch.cli_threshold.load_config", return_value=_make_cfg()), \
         patch("depwatch.cli_threshold.check_dependencies", return_value=statuses):
        result = runner.invoke(threshold_cmd, ["check", "--max-outdated", "1"])
    assert result.exit_code == 1
    assert "[ERROR]" in result.output


def test_check_cmd_shows_warning_but_exits_zero():
    statuses = [_s("requests", True)]
    with patch("depwatch.cli_threshold.load_config", return_value=_make_cfg()), \
         patch("depwatch.cli_threshold.check_dependencies", return_value=statuses):
        result = runner.invoke(threshold_cmd, ["check", "--warn-outdated", "1"])
    assert result.exit_code == 0
    assert "[WARN]" in result.output


def test_check_cmd_project_filter():
    cfg = DepwatchConfig(projects=[
        ProjectConfig(name="alpha", requirements=[]),
        ProjectConfig(name="beta", requirements=[]),
    ])
    statuses: list[DependencyStatus] = []
    call_log: list[str] = []

    def fake_check(reqs):
        call_log.append("called")
        return statuses

    with patch("depwatch.cli_threshold.load_config", return_value=cfg), \
         patch("depwatch.cli_threshold.check_dependencies", side_effect=fake_check):
        result = runner.invoke(threshold_cmd, ["check", "--project", "alpha"])

    assert result.exit_code == 0
    assert len(call_log) == 1
    assert "alpha" in result.output
    assert "beta" not in result.output
