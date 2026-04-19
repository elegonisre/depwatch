"""Tests for depwatch.changelog."""
import json
import pytest
from pathlib import Path
from depwatch.changelog import build_changelog, format_changelog


def _write_history(path: Path, runs: list):
    path.write_text(json.dumps(runs))


@pytest.fixture
def hist(tmp_path):
    return tmp_path / "history.json"


def _rec(project, package, current, latest, outdated):
    return {"project": project, "package": package,
            "current_version": current, "latest_version": latest,
            "is_outdated": outdated}


def test_not_enough_runs_returns_empty(hist):
    _write_history(hist, [{"results": [_rec("proj", "requests", "2.0", "2.1", True)]}])
    assert build_changelog(str(hist)) == []


def test_no_changes_returns_empty(hist):
    run = {"results": [_rec("proj", "requests", "2.0", "2.1", True)]}
    _write_history(hist, [run, run])
    assert build_changelog(str(hist)) == []


def test_detects_new_latest_version(hist):
    r1 = {"results": [_rec("proj", "requests", "2.0", "2.1", True)]}
    r2 = {"results": [_rec("proj", "requests", "2.0", "2.2", True)]}
    _write_history(hist, [r1, r2])
    entries = build_changelog(str(hist))
    assert len(entries) == 1
    e = entries[0]
    assert e.package == "requests"
    assert e.old_latest == "2.1"
    assert e.new_latest == "2.2"


def test_detects_resolved_outdated(hist):
    r1 = {"results": [_rec("proj", "flask", "2.0", "2.1", True)]}
    r2 = {"results": [_rec("proj", "flask", "2.1", "2.1", False)]}
    _write_history(hist, [r1, r2])
    entries = build_changelog(str(hist))
    assert len(entries) == 1
    assert entries[0].is_outdated is False
    assert entries[0].was_outdated is True


def test_skips_package_missing_in_one_run(hist):
    r1 = {"results": [_rec("proj", "requests", "2.0", "2.1", True),
                       _rec("proj", "only-old", "1.0", "1.1", True)]}
    r2 = {"results": [_rec("proj", "requests", "2.0", "2.2", True)]}
    _write_history(hist, [r1, r2])
    entries = build_changelog(str(hist))
    assert all(e.package != "only-old" for e in entries)


def test_format_changelog_no_entries():
    result = format_changelog([])
    assert "No changes" in result


def test_format_changelog_shows_entries(hist):
    r1 = {"results": [_rec("myproject", "django", "3.0", "3.1", True)]}
    r2 = {"results": [_rec("myproject", "django", "3.0", "3.2", True)]}
    _write_history(hist, [r1, r2])
    entries = build_changelog(str(hist))
    text = format_changelog(entries)
    assert "django" in text
    assert "3.1" in text
    assert "3.2" in text
    assert "myproject" in text
