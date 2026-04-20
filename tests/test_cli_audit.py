"""Tests for depwatch.cli_audit."""
from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
from click.testing import CliRunner

from depwatch.cli_audit import audit_cmd
from depwatch.audit import record_audit


@pytest.fixture()
def runner():
    return CliRunner()


def test_log_cmd_empty(runner: CliRunner, tmp_path: Path):
    af = str(tmp_path / "audit.jsonl")
    result = runner.invoke(audit_cmd, ["log", "--file", af])
    assert result.exit_code == 0
    assert "No audit records" in result.output


def test_log_cmd_shows_entries(runner: CliRunner, tmp_path: Path):
    af = tmp_path / "audit.jsonl"
    record_audit("proj1", total=5, outdated=1, audit_file=af)
    result = runner.invoke(audit_cmd, ["log", "--file", str(af)])
    assert result.exit_code == 0
    assert "proj1" in result.output


def test_log_cmd_json_output(runner: CliRunner, tmp_path: Path):
    af = tmp_path / "audit.jsonl"
    record_audit("proj2", total=3, outdated=0, tags=["dev"], audit_file=af)
    result = runner.invoke(audit_cmd, ["log", "--file", str(af), "--json"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert isinstance(data, list)
    assert data[0]["project"] == "proj2"
    assert data[0]["tags"] == ["dev"]


def test_record_cmd(runner: CliRunner, tmp_path: Path):
    cfg_file = tmp_path / "depwatch.toml"
    cfg_file.write_text(
        '[projects]\n[[projects.list]]\nname = "demo"\nrequirements = []\n'
    )
    af = tmp_path / "audit.jsonl"

    mock_cfg = MagicMock()
    mock_project = MagicMock()
    mock_project.name = "demo"
    mock_project.requirements = []
    mock_cfg.projects = [mock_project]

    with patch("depwatch.cli_audit.load_config", return_value=mock_cfg), \
         patch("depwatch.cli_audit.check_dependencies", return_value=[]):
        result = runner.invoke(
            audit_cmd,
            ["record", "--config", str(cfg_file), "--file", str(af), "--triggered-by", "test"]
        )
    assert result.exit_code == 0
    assert "demo" in result.output
    assert af.exists()
