"""Tests for depwatch.cli_watchlist."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest
from click.testing import CliRunner

from depwatch.checker import DependencyStatus
from depwatch.cli_watchlist import watchlist_cmd
from depwatch.watchlist import save_watchlist


@pytest.fixture()
def runner() -> CliRunner:
    return CliRunner()


def _s(pkg: str, current: str, latest: str) -> DependencyStatus:
    return DependencyStatus(
        package=pkg,
        current_version=current,
        latest_version=latest,
        is_outdated=current != latest,
    )


def test_add_cmd(runner: CliRunner, tmp_path: Path) -> None:
    wl = tmp_path / "wl.json"
    with patch("depwatch.cli_watchlist.DEFAULT_WATCHLIST_FILE", wl), \
         patch("depwatch.watchlist.DEFAULT_WATCHLIST_FILE", wl):
        result = runner.invoke(watchlist_cmd, ["add", "requests"])
    assert result.exit_code == 0
    assert "requests" in result.output


def test_remove_cmd(runner: CliRunner, tmp_path: Path) -> None:
    wl = tmp_path / "wl.json"
    save_watchlist(["requests", "flask"], wl)
    with patch("depwatch.cli_watchlist.DEFAULT_WATCHLIST_FILE", wl), \
         patch("depwatch.watchlist.DEFAULT_WATCHLIST_FILE", wl):
        result = runner.invoke(watchlist_cmd, ["remove", "flask"])
    assert result.exit_code == 0
    assert "flask" not in result.output or "Removed" in result.output


def test_list_cmd_empty(runner: CliRunner, tmp_path: Path) -> None:
    wl = tmp_path / "wl.json"
    with patch("depwatch.cli_watchlist.DEFAULT_WATCHLIST_FILE", wl), \
         patch("depwatch.watchlist.DEFAULT_WATCHLIST_FILE", wl):
        result = runner.invoke(watchlist_cmd, ["list"])
    assert result.exit_code == 0
    assert "empty" in result.output.lower()


def test_list_cmd_shows_packages(runner: CliRunner, tmp_path: Path) -> None:
    wl = tmp_path / "wl.json"
    save_watchlist(["django", "flask"], wl)
    with patch("depwatch.cli_watchlist.DEFAULT_WATCHLIST_FILE", wl), \
         patch("depwatch.watchlist.DEFAULT_WATCHLIST_FILE", wl):
        result = runner.invoke(watchlist_cmd, ["list"])
    assert "django" in result.output
    assert "flask" in result.output


def test_check_cmd(runner: CliRunner, tmp_path: Path) -> None:
    wl = tmp_path / "wl.json"
    save_watchlist(["requests"], wl)
    statuses = [_s("requests", "2.28.0", "2.31.0")]
    with patch("depwatch.cli_watchlist.load_config") as mock_cfg, \
         patch("depwatch.cli_watchlist.check_dependencies", return_value=statuses), \
         patch("depwatch.cli_watchlist.filter_watchlist", return_value=statuses):
        mock_cfg.return_value.projects = [type("P", (), {"requirements": []})()] 
        result = runner.invoke(watchlist_cmd, ["check", "--config", "depwatch.toml"])
    assert result.exit_code == 0
