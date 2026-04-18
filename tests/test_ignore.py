"""Tests for depwatch.ignore and depwatch.cli_ignore."""
import json
import pytest
from pathlib import Path
from click.testing import CliRunner
from depwatch.ignore import load_ignore_list, save_ignore_list, add_to_ignore, remove_from_ignore
from depwatch.cli_ignore import ignore_cmd


@pytest.fixture
def ig(tmp_path):
    return tmp_path / "ignore.json"


def test_load_missing_file(ig):
    assert load_ignore_list(ig) == []


def test_save_and_load(ig):
    save_ignore_list(["requests", "flask"], ig)
    result = load_ignore_list(ig)
    assert result == ["flask", "requests"]  # sorted


def test_add_new_package(ig):
    result = add_to_ignore("django", ig)
    assert "django" in result


def test_add_duplicate_is_idempotent(ig):
    add_to_ignore("django", ig)
    result = add_to_ignore("django", ig)
    assert result.count("django") == 1


def test_remove_package(ig):
    save_ignore_list(["requests", "flask"], ig)
    result = remove_from_ignore("flask", ig)
    assert "flask" not in result
    assert "requests" in result


def test_remove_nonexistent_is_safe(ig):
    save_ignore_list(["requests"], ig)
    result = remove_from_ignore("nonexistent", ig)
    assert result == ["requests"]


# CLI tests

def test_cli_add(ig):
    runner = CliRunner()
    result = runner.invoke(ignore_cmd, ["add", "boto3", "--file", str(ig)])
    assert result.exit_code == 0
    assert "boto3" in result.output


def test_cli_remove(ig):
    save_ignore_list(["boto3"], ig)
    runner = CliRunner()
    result = runner.invoke(ignore_cmd, ["remove", "boto3", "--file", str(ig)])
    assert result.exit_code == 0
    assert "boto3" in result.output


def test_cli_list_empty(ig):
    runner = CliRunner()
    result = runner.invoke(ignore_cmd, ["list", "--file", str(ig)])
    assert result.exit_code == 0
    assert "No packages" in result.output


def test_cli_list_with_packages(ig):
    save_ignore_list(["requests", "flask"], ig)
    runner = CliRunner()
    result = runner.invoke(ignore_cmd, ["list", "--file", str(ig)])
    assert "requests" in result.output
    assert "flask" in result.output
