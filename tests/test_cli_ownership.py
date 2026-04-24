"""Tests for depwatch.cli_ownership commands."""
from __future__ import annotations

import json
from pathlib import Path

import pytest
from click.testing import CliRunner

from depwatch.cli_ownership import ownership_cmd


@pytest.fixture()
def runner() -> CliRunner:
    return CliRunner()


def _file(tmp_path: Path) -> str:
    return str(tmp_path / "ownership.json")


def test_assign_cmd_creates_entry(runner: CliRunner, tmp_path: Path) -> None:
    f = _file(tmp_path)
    result = runner.invoke(
        ownership_cmd, ["assign", "myproj", "requests", "alice", "--file", f]
    )
    assert result.exit_code == 0
    assert "Assigned" in result.output
    data = json.loads(Path(f).read_text())
    assert "alice" in data["myproj"]["requests"]


def test_assign_cmd_idempotent(runner: CliRunner, tmp_path: Path) -> None:
    f = _file(tmp_path)
    runner.invoke(ownership_cmd, ["assign", "p", "pkg", "alice", "--file", f])
    runner.invoke(ownership_cmd, ["assign", "p", "pkg", "alice", "--file", f])
    data = json.loads(Path(f).read_text())
    assert data["p"]["pkg"].count("alice") == 1


def test_remove_cmd(runner: CliRunner, tmp_path: Path) -> None:
    f = _file(tmp_path)
    runner.invoke(ownership_cmd, ["assign", "p", "pkg", "alice", "--file", f])
    result = runner.invoke(ownership_cmd, ["remove", "p", "pkg", "alice", "--file", f])
    assert result.exit_code == 0
    data = json.loads(Path(f).read_text())
    assert "alice" not in data["p"]["pkg"]


def test_list_cmd_shows_owners(runner: CliRunner, tmp_path: Path) -> None:
    f = _file(tmp_path)
    runner.invoke(ownership_cmd, ["assign", "p", "pkg", "alice", "--file", f])
    runner.invoke(ownership_cmd, ["assign", "p", "pkg", "bob", "--file", f])
    result = runner.invoke(ownership_cmd, ["list", "p", "pkg", "--file", f])
    assert result.exit_code == 0
    assert "alice" in result.output
    assert "bob" in result.output


def test_list_cmd_no_owners(runner: CliRunner, tmp_path: Path) -> None:
    f = _file(tmp_path)
    result = runner.invoke(ownership_cmd, ["list", "p", "pkg", "--file", f])
    assert result.exit_code == 0
    assert "No owners" in result.output


def test_by_owner_cmd(runner: CliRunner, tmp_path: Path) -> None:
    f = _file(tmp_path)
    runner.invoke(ownership_cmd, ["assign", "proj_a", "requests", "alice", "--file", f])
    runner.invoke(ownership_cmd, ["assign", "proj_b", "django", "alice", "--file", f])
    result = runner.invoke(ownership_cmd, ["by-owner", "alice", "--file", f])
    assert result.exit_code == 0
    assert "proj_a" in result.output
    assert "proj_b" in result.output


def test_by_owner_cmd_none_found(runner: CliRunner, tmp_path: Path) -> None:
    f = _file(tmp_path)
    result = runner.invoke(ownership_cmd, ["by-owner", "nobody", "--file", f])
    assert result.exit_code == 0
    assert "No packages found" in result.output
