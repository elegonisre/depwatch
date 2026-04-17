"""Tests for depwatch.cli_baseline commands."""
import json
from pathlib import Path
from unittest.mock import patch, MagicMock

from click.testing import CliRunner

from depwatch.cli_baseline import baseline_cmd
from depwatch.checker import DependencyStatus


def _s(pkg, cur, lat, out):
    return DependencyStatus(package=pkg, current_version=cur, latest_version=lat, outdated=out)


CFG_TOML = """
[project]
name = "myapp"
packages = ["requests"]
"""


def _write_cfg(tmp_path: Path) -> Path:
    p = tmp_path / "depwatch.toml"
    p.write_text(CFG_TOML)
    return p


def test_save_cmd(tmp_path):
    cfg = _write_cfg(tmp_path)
    bf = tmp_path / "baseline.json"
    statuses = [_s("requests", "2.28.0", "2.31.0", True)]
    with patch("depwatch.cli_baseline.load_config") as lc, \
         patch("depwatch.cli_baseline.check_dependencies", return_value=statuses):
        proj = MagicMock(name="myapp", packages=["requests"])
        proj.name = "myapp"
        lc.return_value.projects = [proj]
        runner = CliRunner()
        result = runner.invoke(baseline_cmd, ["save", "--config", str(cfg), "--baseline-file", str(bf)])
    assert result.exit_code == 0
    assert "myapp" in result.output
    assert bf.exists()


def test_show_cmd_no_baseline(tmp_path):
    bf = tmp_path / "baseline.json"
    runner = CliRunner()
    result = runner.invoke(baseline_cmd, ["show", "myapp", "--baseline-file", str(bf)])
    assert "No baseline found" in result.output


def test_show_cmd_with_data(tmp_path):
    bf = tmp_path / "baseline.json"
    bf.write_text(json.dumps({"myapp": {"saved_at": "2024-01-01T00:00:00+00:00", "packages": [
        {"package": "requests", "current": "2.28.0", "latest": "2.31.0", "outdated": True}
    ]}}))
    runner = CliRunner()
    result = runner.invoke(baseline_cmd, ["show", "myapp", "--baseline-file", str(bf)])
    assert "requests" in result.output
    assert "OUTDATED" in result.output


def test_diff_cmd_no_changes(tmp_path):
    cfg = _write_cfg(tmp_path)
    bf = tmp_path / "baseline.json"
    statuses = [_s("requests", "2.31.0", "2.31.0", False)]
    with patch("depwatch.cli_baseline.load_config") as lc, \
         patch("depwatch.cli_baseline.check_dependencies", return_value=statuses), \
         patch("depwatch.cli_baseline.diff_from_baseline",
               return_value={"new_outdated": [], "resolved": [], "version_changed": []}):
        proj = MagicMock()
        proj.name = "myapp"
        lc.return_value.projects = [proj]
        runner = CliRunner()
        result = runner.invoke(baseline_cmd, ["diff", "--config", str(cfg), "--baseline-file", str(bf)])
    assert "No changes from baseline" in result.output
