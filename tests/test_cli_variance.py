"""Tests for depwatch.cli_variance."""
from __future__ import annotations

import json
import pathlib

import pytest
from click.testing import CliRunner

from depwatch.cli_variance import variance_cmd


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _rec(project: str, pkg: str, installed: str, latest: str, ts: str = "2024-01-01T00:00:00") -> dict:
    return {
        "project": project,
        "package": pkg,
        "installed_version": installed,
        "latest_version": latest,
        "timestamp": ts,
    }


@pytest.fixture()
def runner():
    return CliRunner()


@pytest.fixture()
def setup(tmp_path: pathlib.Path):
    """Write a minimal config + history and return their paths."""
    history_file = tmp_path / "history.json"
    records = [
        _rec("proj", "requests", "2.0", "2.1", "2024-01-01T00:00:00"),
        _rec("proj", "flask", "1.0", "1.0", "2024-01-01T00:00:00"),
        _rec("proj", "requests", "2.1", "2.1", "2024-01-02T00:00:00"),
        _rec("proj", "flask", "1.0", "2.0", "2024-01-02T00:00:00"),
    ]
    history_file.write_text(json.dumps(records))

    cfg_file = tmp_path / "depwatch.toml"
    cfg_file.write_text(
        f'[depwatch]\nhistory_file = "{history_file}"\n'
        '[projects]\n[[projects.list]]\nname = "proj"\nrequirements = "requirements.txt"\n'
    )
    return str(cfg_file), str(history_file)


# ---------------------------------------------------------------------------
# tests
# ---------------------------------------------------------------------------

def test_show_cmd_text(runner, setup):
    cfg_path, _ = setup
    result = runner.invoke(variance_cmd, ["show", "--config", cfg_path])
    assert result.exit_code == 0
    assert "proj" in result.output


def test_show_cmd_json(runner, setup):
    cfg_path, _ = setup
    result = runner.invoke(variance_cmd, ["show", "--config", cfg_path, "--format", "json"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert isinstance(data, list)
    assert data[0]["project"] == "proj"
    assert "std_dev" in data[0]
    assert "stability_label" in data[0]


def test_show_cmd_single_project(runner, setup):
    cfg_path, _ = setup
    result = runner.invoke(variance_cmd, ["show", "--config", cfg_path, "--project", "proj"])
    assert result.exit_code == 0
    assert "proj" in result.output


def test_show_cmd_unknown_project_empty(runner, setup):
    cfg_path, _ = setup
    result = runner.invoke(variance_cmd, ["show", "--config", cfg_path, "--project", "ghost"])
    assert result.exit_code == 0
    assert "No variance data" in result.output
