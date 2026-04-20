"""Tests for depwatch.cli_suppress."""
from __future__ import annotations

from datetime import datetime, timezone, timedelta
from pathlib import Path
from unittest.mock import patch

from click.testing import CliRunner

from depwatch.cli_suppress import suppress_cmd
from depwatch.suppress import suppress_package, load_suppressions


def _runner():
    return CliRunner()


def test_add_cmd_creates_suppression(tmp_path):
    sf = tmp_path / "s.json"
    with patch("depwatch.suppress.DEFAULT_SUPPRESS_FILE", sf), \
         patch("depwatch.cli_suppress.suppress_package") as mock_sup:
        result = _runner().invoke(suppress_cmd, ["add", "requests", "--days", "3", "--reason", "testing"])
    assert result.exit_code == 0
    assert "requests" in result.output
    mock_sup.assert_called_once()
    _, kwargs = mock_sup.call_args[0], mock_sup.call_args
    assert kwargs[0][0] == "requests"


def test_remove_cmd_existing(tmp_path):
    sf = tmp_path / "s.json"
    until = datetime.now(timezone.utc) + timedelta(days=5)
    suppress_package("flask", until, path=sf)
    with patch("depwatch.cli_suppress.remove_suppression") as mock_rm:
        mock_rm.return_value = True
        result = _runner().invoke(suppress_cmd, ["remove", "flask"])
    assert result.exit_code == 0
    assert "removed" in result.output


def test_remove_cmd_missing(tmp_path):
    with patch("depwatch.cli_suppress.remove_suppression") as mock_rm:
        mock_rm.return_value = False
        result = _runner().invoke(suppress_cmd, ["remove", "ghost"])
    assert "No suppression" in result.output


def test_list_cmd_empty(tmp_path):
    with patch("depwatch.cli_suppress.list_suppressions", return_value=[]):
        result = _runner().invoke(suppress_cmd, ["list"])
    assert "No suppressions" in result.output


def test_list_cmd_shows_entries(tmp_path):
    entries = [
        {"package": "django", "until": datetime(2099, 1, 1, tzinfo=timezone.utc), "reason": "", "active": True},
    ]
    with patch("depwatch.cli_suppress.list_suppressions", return_value=entries):
        result = _runner().invoke(suppress_cmd, ["list"])
    assert "django" in result.output
    assert "active" in result.output
