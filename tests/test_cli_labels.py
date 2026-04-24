"""Tests for depwatch.cli_labels."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest
from click.testing import CliRunner

from depwatch.cli_labels import labels_cmd


@pytest.fixture()
def runner() -> CliRunner:
    return CliRunner()


def _patch_path(tmp_path: Path):
    lf = tmp_path / "labels.json"
    return patch("depwatch.labels.DEFAULT_LABELS_FILE", lf)


def test_add_cmd(runner: CliRunner, tmp_path: Path) -> None:
    lf = tmp_path / "labels.json"
    with patch("depwatch.cli_labels.add_label") as mock_add:
        result = runner.invoke(labels_cmd, ["add", "requests", "network"])
    assert result.exit_code == 0
    assert "added" in result.output
    mock_add.assert_called_once_with("requests", "network")


def test_remove_cmd(runner: CliRunner) -> None:
    with patch("depwatch.cli_labels.remove_label") as mock_rm:
        result = runner.invoke(labels_cmd, ["remove", "requests", "network"])
    assert result.exit_code == 0
    assert "removed" in result.output
    mock_rm.assert_called_once_with("requests", "network")


def test_list_cmd_empty(runner: CliRunner) -> None:
    with patch("depwatch.cli_labels.load_labels", return_value={}):
        result = runner.invoke(labels_cmd, ["list"])
    assert result.exit_code == 0
    assert "No labels" in result.output


def test_list_cmd_all(runner: CliRunner) -> None:
    fake = {"requests": ["network"], "flask": ["web"]}
    with patch("depwatch.cli_labels.load_labels", return_value=fake):
        result = runner.invoke(labels_cmd, ["list"])
    assert "requests" in result.output
    assert "network" in result.output
    assert "flask" in result.output


def test_list_cmd_single_package(runner: CliRunner) -> None:
    with patch("depwatch.cli_labels.get_labels", return_value=["critical"]):
        result = runner.invoke(labels_cmd, ["list", "requests"])
    assert "critical" in result.output


def test_list_cmd_single_package_no_labels(runner: CliRunner) -> None:
    with patch("depwatch.cli_labels.get_labels", return_value=[]):
        result = runner.invoke(labels_cmd, ["list", "requests"])
    assert "No labels" in result.output


def test_filter_cmd_matches(runner: CliRunner) -> None:
    with patch("depwatch.cli_labels.filter_by_label", return_value=["requests"]):
        result = runner.invoke(labels_cmd, ["filter", "network", "requests", "flask"])
    assert "requests" in result.output


def test_filter_cmd_no_match(runner: CliRunner) -> None:
    with patch("depwatch.cli_labels.filter_by_label", return_value=[]):
        result = runner.invoke(labels_cmd, ["filter", "network", "flask"])
    assert "No packages matched" in result.output
