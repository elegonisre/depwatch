"""Tests for depwatch.cli_dependency_age."""
from __future__ import annotations

import json
from unittest.mock import patch, MagicMock

from click.testing import CliRunner

from depwatch.cli_dependency_age import dep_age_cmd
from depwatch.checker import DependencyStatus
from depwatch.dependency_age import DependencyAge
from depwatch.config import DepwatchConfig, ProjectConfig


def _s(pkg, installed, latest, outdated=True) -> DependencyStatus:
    return DependencyStatus(
        package=pkg,
        installed_version=installed,
        latest_version=latest,
        is_outdated=outdated,
    )


def _make_cfg() -> DepwatchConfig:
    return DepwatchConfig(
        projects=[ProjectConfig(name="myproject", requirements=["django==3.2"])],
        alert=None,
    )


_ENTRIES = [
    DependencyAge("myproject", "django", "3.2", "4.2", None, None, 400, True),
]


def test_show_cmd_text():
    runner = CliRunner()
    with patch("depwatch.cli_dependency_age.load_config", return_value=_make_cfg()), \
         patch("depwatch.cli_dependency_age.check_dependencies", return_value=[_s("django", "3.2", "4.2")]), \
         patch("depwatch.cli_dependency_age.compute_dependency_ages", return_value=_ENTRIES):
        result = runner.invoke(dep_age_cmd, ["show"])
    assert result.exit_code == 0
    assert "django" in result.output


def test_show_cmd_json():
    runner = CliRunner()
    with patch("depwatch.cli_dependency_age.load_config", return_value=_make_cfg()), \
         patch("depwatch.cli_dependency_age.check_dependencies", return_value=[_s("django", "3.2", "4.2")]), \
         patch("depwatch.cli_dependency_age.compute_dependency_ages", return_value=_ENTRIES):
        result = runner.invoke(dep_age_cmd, ["show", "--format", "json"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert isinstance(data, list)
    assert data[0]["package"] == "django"
    assert data[0]["days_behind"] == 400


def test_show_cmd_outdated_only_filters():
    mixed = [
        DependencyAge("myproject", "django", "3.2", "4.2", None, None, 400, True),
        DependencyAge("myproject", "flask", "2.3", "2.3", None, None, 0, False),
    ]
    runner = CliRunner()
    with patch("depwatch.cli_dependency_age.load_config", return_value=_make_cfg()), \
         patch("depwatch.cli_dependency_age.check_dependencies", return_value=[]), \
         patch("depwatch.cli_dependency_age.compute_dependency_ages", return_value=mixed):
        result = runner.invoke(dep_age_cmd, ["show", "--outdated-only", "--format", "json"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert all(d["is_outdated"] for d in data)
    assert len(data) == 1


def test_show_cmd_missing_config():
    runner = CliRunner()
    with patch("depwatch.cli_dependency_age.load_config", side_effect=FileNotFoundError):
        result = runner.invoke(dep_age_cmd, ["show"])
    assert result.exit_code != 0
    assert "not found" in result.output.lower() or "Error" in result.output


def test_show_cmd_unknown_project():
    runner = CliRunner()
    with patch("depwatch.cli_dependency_age.load_config", return_value=_make_cfg()):
        result = runner.invoke(dep_age_cmd, ["show", "--project", "nonexistent"])
    assert result.exit_code != 0
