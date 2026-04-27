"""Tests for depwatch.health."""
from __future__ import annotations

from unittest.mock import patch

from depwatch.checker import DependencyStatus
from depwatch.health import HealthReport, _grade, compute_health, format_health_report


def _s(name: str, current: str, latest: str) -> DependencyStatus:
    return DependencyStatus(
        name=name,
        current_version=current,
        latest_version=latest,
        is_outdated=(current != latest),
    )


# ---------------------------------------------------------------------------
# _grade
# ---------------------------------------------------------------------------

def test_grade_a():
    assert _grade(95) == "A"


def test_grade_b():
    assert _grade(80) == "B"


def test_grade_c():
    assert _grade(60) == "C"


def test_grade_d():
    assert _grade(45) == "D"


def test_grade_f():
    assert _grade(20) == "F"


# ---------------------------------------------------------------------------
# compute_health – empty
# ---------------------------------------------------------------------------

def test_compute_health_empty():
    r = compute_health("proj", [])
    assert r.total == 0
    assert r.score == 100.0
    assert r.grade == "A"


# ---------------------------------------------------------------------------
# compute_health – all up-to-date
# ---------------------------------------------------------------------------

def test_compute_health_all_up_to_date():
    statuses = [_s("requests", "2.31.0", "2.31.0"), _s("click", "8.1.0", "8.1.0")]
    with patch("depwatch.health.find_stale", return_value=[]), \
         patch("depwatch.health.assess_risk", return_value=[]):
        r = compute_health("myproject", statuses)
    assert r.outdated == 0
    assert r.high_risk == 0
    assert r.stale == 0
    assert r.score == 100.0
    assert r.grade == "A"


# ---------------------------------------------------------------------------
# compute_health – penalties applied
# ---------------------------------------------------------------------------

def test_compute_health_penalties_reduce_score():
    from depwatch.risk import RiskEntry
    statuses = [_s("django", "3.0.0", "4.2.0")]
    mock_risk = [RiskEntry(name="django", current="3.0.0", latest="4.2.0",
                           score=80, label="high")]
    mock_stale = [object()]  # one stale entry

    with patch("depwatch.health.assess_risk", return_value=mock_risk), \
         patch("depwatch.health.find_stale", return_value=mock_stale), \
         patch("depwatch.health.compute_score") as mock_cs:
        from depwatch.score import ProjectScore
        mock_cs.return_value = ProjectScore(
            project="p", total=1, outdated=1, score=60.0, grade="C"
        )
        r = compute_health("p", statuses)

    # penalty = 1 high-risk * 2 + 1 stale * 1 = 3 → 60 - 3 = 57
    assert r.score == 57.0
    assert r.high_risk == 1
    assert r.stale == 1


# ---------------------------------------------------------------------------
# compute_health – score floor is 0
# ---------------------------------------------------------------------------

def test_compute_health_score_floor():
    from depwatch.risk import RiskEntry
    statuses = [_s(f"pkg{i}", "1.0", "2.0") for i in range(20)]
    mock_risk = [
        RiskEntry(name=f"pkg{i}", current="1.0", latest="2.0", score=90, label="critical")
        for i in range(20)
    ]
    with patch("depwatch.health.assess_risk", return_value=mock_risk), \
         patch("depwatch.health.find_stale", return_value=[]), \
         patch("depwatch.health.compute_score") as mock_cs:
        from depwatch.score import ProjectScore
        mock_cs.return_value = ProjectScore(
            project="p", total=20, outdated=20, score=10.0, grade="F"
        )
        r = compute_health("p", statuses)
    assert r.score >= 0.0


# ---------------------------------------------------------------------------
# format_health_report
# ---------------------------------------------------------------------------

def test_format_health_report_text():
    reports = [
        HealthReport("proj", 5, 2, 1, 0, 78.0, "B", "2/5 outdated")
    ]
    out = format_health_report(reports, fmt="text")
    assert "proj" in out
    assert "Grade: B" in out
    assert "78.0/100" in out


def test_format_health_report_json():
    import json
    reports = [
        HealthReport("proj", 5, 2, 1, 0, 78.0, "B", "2/5 outdated")
    ]
    out = format_health_report(reports, fmt="json")
    data = json.loads(out)
    assert isinstance(data, list)
    assert data[0]["project"] == "proj"
    assert data[0]["score"] == 78.0
    assert data[0]["grade"] == "B"
