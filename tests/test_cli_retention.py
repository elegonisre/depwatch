"""Tests for depwatch.cli_retention."""
from __future__ import annotations

import json
from datetime import datetime, timezone, timedelta
from pathlib import Path

import pytest
from click.testing import CliRunner

from depwatch.cli_retention import retention_cmd


def _ts(days_ago: int) -> str:
    return (datetime.now(timezone.utc) - timedelta(days=days_ago)).isoformat()


def _write(path: Path, records: list) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as fh:
        json.dump(records, fh)


@pytest.fixture()
def runner() -> CliRunner:
    return CliRunner()


def test_prune_cmd_removes_old_entries(runner: CliRunner, tmp_path: Path) -> None:
    hf = tmp_path / "hist.json"
    _write(hf, [
        {"timestamp": _ts(200), "project": "old"},
        {"timestamp": _ts(5), "project": "new"},
    ])
    result = runner.invoke(
        retention_cmd, ["prune", "--max-days", "30", "--history-file", str(hf)]
    )
    assert result.exit_code == 0
    assert "1" in result.output  # removed count


def test_prune_cmd_nothing_to_remove(runner: CliRunner, tmp_path: Path) -> None:
    hf = tmp_path / "hist.json"
    _write(hf, [{"timestamp": _ts(3), "project": "fresh"}])
    result = runner.invoke(
        retention_cmd, ["prune", "--max-days", "30", "--history-file", str(hf)]
    )
    assert result.exit_code == 0
    assert "0" in result.output


def test_prune_cmd_quiet_flag_suppresses_output(runner: CliRunner, tmp_path: Path) -> None:
    hf = tmp_path / "hist.json"
    _write(hf, [{"timestamp": _ts(5), "project": "x"}])
    result = runner.invoke(
        retention_cmd,
        ["prune", "--max-days", "30", "--history-file", str(hf), "--quiet"],
    )
    assert result.output.strip() == ""


def test_prune_cmd_missing_history_file_is_ok(runner: CliRunner, tmp_path: Path) -> None:
    hf = tmp_path / "nonexistent.json"
    result = runner.invoke(
        retention_cmd, ["prune", "--max-days", "30", "--history-file", str(hf)]
    )
    assert result.exit_code == 0
