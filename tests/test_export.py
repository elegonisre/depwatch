"""Tests for depwatch.export."""
from __future__ import annotations

import csv
import io
import json

import pytest

from depwatch.checker import DependencyStatus
from depwatch.export import export_results, to_csv, to_json


def _s(package: str, current: str, latest: str, outdated: bool) -> DependencyStatus:
    return DependencyStatus(
        package=package,
        current_version=current,
        latest_version=latest,
        outdated=outdated,
    )


STATUSES = [
    _s("requests", "2.28.0", "2.31.0", True),
    _s("click", "8.1.3", "8.1.3", False),
]


def test_to_csv_headers():
    result = to_csv("myproject", STATUSES)
    reader = csv.DictReader(io.StringIO(result))
    assert reader.fieldnames == ["project", "package", "current_version", "latest_version", "outdated"]


def test_to_csv_rows():
    result = to_csv("myproject", STATUSES)
    rows = list(csv.DictReader(io.StringIO(result)))
    assert len(rows) == 2
    assert rows[0]["package"] == "requests"
    assert rows[0]["outdated"] == "True"
    assert rows[1]["package"] == "click"
    assert rows[1]["project"] == "myproject"


def test_to_json_structure():
    result = to_json("myproject", STATUSES)
    data = json.loads(result)
    assert isinstance(data, list)
    assert len(data) == 2
    assert data[0]["package"] == "requests"
    assert data[0]["outdated"] is True
    assert data[1]["outdated"] is False


def test_export_results_csv():
    result = export_results("proj", STATUSES, "csv")
    assert "requests" in result
    assert "click" in result


def test_export_results_json():
    result = export_results("proj", STATUSES, "json")
    data = json.loads(result)
    assert data[0]["project"] == "proj"


def test_export_results_invalid_format():
    with pytest.raises(ValueError, match="Unsupported export format"):
        export_results("proj", STATUSES, "xml")


def test_export_empty_statuses_csv():
    result = export_results("proj", [], "csv")
    rows = list(csv.DictReader(io.StringIO(result)))
    assert rows == []


def test_export_empty_statuses_json():
    result = export_results("proj", [], "json")
    assert json.loads(result) == []
