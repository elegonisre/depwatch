"""Tests for depwatch.reporter."""
import json
from depwatch.checker import DependencyStatus
from depwatch.reporter import generate_report


def _make_statuses():
    return [
        DependencyStatus(package="requests", current_version="2.28.0", latest_version="2.31.0", is_outdated=True),
        DependencyStatus(package="flask", current_version="3.0.0", latest_version="3.0.0", is_outdated=False),
        DependencyStatus(package="click", current_version="8.0.0", latest_version="8.1.7", is_outdated=True),
    ]


def test_text_report_contains_project_name():
    report = generate_report("my-project", _make_statuses(), fmt="text")
    assert "my-project" in report


def test_text_report_shows_outdated():
    report = generate_report("proj", _make_statuses(), fmt="text")
    assert "requests" in report
    assert "2.28.0" in report
    assert "2.31.0" in report


def test_text_report_shows_up_to_date():
    report = generate_report("proj", _make_statuses(), fmt="text")
    assert "flask" in report


def test_text_report_summary_counts():
    report = generate_report("proj", _make_statuses(), fmt="text")
    assert "Total: 3" in report
    assert "Outdated: 2" in report


def test_text_report_all_up_to_date():
    statuses = [
        DependencyStatus(package="flask", current_version="3.0.0", latest_version="3.0.0", is_outdated=False),
    ]
    report = generate_report("proj", statuses, fmt="text")
    assert "All dependencies are up to date." in report


def test_json_report_structure():
    report = generate_report("proj", _make_statuses(), fmt="json")
    data = json.loads(report)
    assert data["project"] == "proj"
    assert data["total"] == 3
    assert data["outdated_count"] == 2
    assert len(data["dependencies"]) == 3


def test_json_report_dependency_fields():
    report = generate_report("proj", _make_statuses(), fmt="json")
    data = json.loads(report)
    dep = next(d for d in data["dependencies"] if d["package"] == "requests")
    assert dep["current_version"] == "2.28.0"
    assert dep["latest_version"] == "2.31.0"
    assert dep["is_outdated"] is True


def test_json_report_generated_field_present():
    report = generate_report("proj", _make_statuses(), fmt="json")
    data = json.loads(report)
    assert "generated" in data
