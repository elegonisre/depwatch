"""Tests for depwatch.cli_cadence."""
import json
from pathlib import Path

import pytest
from click.testing import CliRunner

from depwatch.cli_cadence import cadence_cmd


@pytest.fixture
def runner():
    return CliRunner()


def _write_history(path: Path, records: list) -> None:
    path.write_text(json.dumps(records))


def test_show_cmd_text_output(runner, tmp_path):
    hist = tmp_path / "h.json"
    _write_history(
        hist,
        [
            {"project": "svc", "timestamp": "2024-05-01T06:00:00", "statuses": []},
            {"project": "svc", "timestamp": "2024-05-01T18:00:00", "statuses": []},
        ],
    )
    result = runner.invoke(cadence_cmd, ["show", "--history", str(hist)])
    assert result.exit_code == 0
    assert "svc" in result.output
    assert "2 runs" in result.output


def test_show_cmd_json_output(runner, tmp_path):
    hist = tmp_path / "h.json"
    _write_history(
        hist,
        [
            {"project": "api", "timestamp": "2024-06-01T00:00:00", "statuses": []},
            {"project": "api", "timestamp": "2024-06-02T00:00:00", "statuses": []},
        ],
    )
    result = runner.invoke(
        cadence_cmd, ["show", "--history", str(hist), "--format", "json"]
    )
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert len(data) == 1
    assert data[0]["project"] == "api"
    assert data[0]["run_count"] == 2
    assert data[0]["avg_interval_hours"] == pytest.approx(24.0)


def test_show_cmd_min_runs_filter(runner, tmp_path):
    hist = tmp_path / "h.json"
    _write_history(
        hist,
        [
            {"project": "rare", "timestamp": "2024-01-01T00:00:00", "statuses": []},
            {"project": "common", "timestamp": "2024-01-01T00:00:00", "statuses": []},
            {"project": "common", "timestamp": "2024-01-02T00:00:00", "statuses": []},
        ],
    )
    result = runner.invoke(
        cadence_cmd, ["show", "--history", str(hist), "--min-runs", "2"]
    )
    assert result.exit_code == 0
    assert "common" in result.output
    assert "rare" not in result.output


def test_show_cmd_empty_history(runner, tmp_path):
    hist = tmp_path / "h.json"
    hist.write_text("[]")
    result = runner.invoke(cadence_cmd, ["show", "--history", str(hist)])
    assert result.exit_code == 0
    assert "No cadence data" in result.output
