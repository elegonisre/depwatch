"""Tests for depwatch.score."""
import pytest
from depwatch.checker import DependencyStatus
from depwatch.score import compute_score, score_all, format_scores, _grade


def _s(name, current, latest, outdated):
    return DependencyStatus(
        name=name, current_version=current, latest_version=latest, outdated=outdated
    )


def test_compute_score_all_up_to_date():
    statuses = [_s("requests", "2.0", "2.0", False), _s("flask", "1.0", "1.0", False)]
    result = compute_score("myapp", statuses)
    assert result.score == 100.0
    assert result.grade == "A"
    assert result.outdated == 0


def test_compute_score_all_outdated():
    statuses = [_s("requests", "1.0", "2.0", True), _s("flask", "0.9", "1.0", True)]
    result = compute_score("myapp", statuses)
    assert result.score == 0.0
    assert result.grade == "F"
    assert result.outdated == 2


def test_compute_score_partial():
    statuses = [
        _s("requests", "1.0", "2.0", True),
        _s("flask", "1.0", "1.0", False),
        _s("django", "3.0", "3.0", False),
        _s("click", "7.0", "8.0", True),
    ]
    result = compute_score("myapp", statuses)
    assert result.score == 50.0
    assert result.grade == "F"
    assert result.total == 4


def test_compute_score_empty():
    result = compute_score("empty", [])
    assert result.score == 100.0
    assert result.grade == "A"
    assert result.total == 0


def test_grade_boundaries():
    assert _grade(95) == "A"
    assert _grade(90) == "A"
    assert _grade(89) == "B"
    assert _grade(75) == "B"
    assert _grade(74) == "C"
    assert _grade(60) == "C"
    assert _grade(59) == "D"
    assert _grade(40) == "D"
    assert _grade(39) == "F"


def test_score_all_multiple_projects():
    results = {
        "proj_a": [_s("requests", "1.0", "2.0", True)],
        "proj_b": [_s("flask", "1.0", "1.0", False)],
    }
    scores = score_all(results)
    assert len(scores) == 2
    by_name = {s.project: s for s in scores}
    assert by_name["proj_a"].score == 0.0
    assert by_name["proj_b"].score == 100.0


def test_format_scores_contains_project():
    results = {"myapp": [_s("requests", "1.0", "1.0", False)]}
    scores = score_all(results)
    output = format_scores(scores)
    assert "myapp" in output
    assert "100.0%" in output
    assert "A" in output
