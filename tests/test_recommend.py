"""Tests for depwatch.recommend."""
from __future__ import annotations

from unittest.mock import patch, MagicMock

import pytest

from depwatch.checker import DependencyStatus
from depwatch.recommend import (
    Recommendation,
    build_recommendations,
    format_recommendations,
    _priority,
)


def _s(pkg, current, latest, project="proj"):
    return DependencyStatus(
        project=project,
        package=pkg,
        current_version=current,
        latest_version=latest,
        is_up_to_date=(current == latest),
    )


def _mock_risk(statuses):
    """Return fake RiskEntry objects without calling real assess_risk."""
    from depwatch.risk import RiskEntry
    results = []
    for s in statuses:
        if not s.is_up_to_date:
            results.append(
                RiskEntry(
                    project=s.project,
                    package=s.package,
                    current_version=s.current_version,
                    latest_version=s.latest_version,
                    major_gap=1,
                    minor_gap=0,
                    patch_gap=0,
                    risk_score=80,
                    risk_label="high",
                )
            )
    return results


@patch("depwatch.recommend.assess_risk", side_effect=_mock_risk)
def test_build_recommendations_excludes_up_to_date(mock_risk):
    statuses = [_s("django", "3.0.0", "4.0.0"), _s("flask", "2.0.0", "2.0.0")]
    recs = build_recommendations(statuses)
    assert len(recs) == 1
    assert recs[0].package == "django"


@patch("depwatch.recommend.assess_risk", side_effect=_mock_risk)
def test_build_recommendations_sorted_by_priority(mock_risk):
    statuses = [
        _s("aaa", "1.0", "2.0", project="p1"),
        _s("bbb", "1.0", "2.0", project="p2"),
    ]
    recs = build_recommendations(statuses)
    # Both are "high"; should be sorted by project then package
    assert recs[0].project == "p1"
    assert recs[1].project == "p2"


@patch("depwatch.recommend.assess_risk", side_effect=_mock_risk)
def test_build_recommendations_top_n(mock_risk):
    statuses = [_s(f"pkg{i}", "1.0", "2.0") for i in range(5)]
    recs = build_recommendations(statuses, top_n=2)
    assert len(recs) == 2


@patch("depwatch.recommend.assess_risk", return_value=[])
def test_build_recommendations_all_up_to_date(mock_risk):
    statuses = [_s("requests", "2.28.0", "2.28.0")]
    recs = build_recommendations(statuses)
    assert recs == []


def test_priority_mapping():
    assert _priority("critical") < _priority("high")
    assert _priority("high") < _priority("medium")
    assert _priority("medium") < _priority("low")
    assert _priority("unknown") == 5


@patch("depwatch.recommend.assess_risk", side_effect=_mock_risk)
def test_format_recommendations_non_empty(mock_risk):
    statuses = [_s("django", "3.0.0", "4.0.0")]
    recs = build_recommendations(statuses)
    output = format_recommendations(recs)
    assert "django" in output
    assert "HIGH" in output


def test_format_recommendations_empty():
    output = format_recommendations([])
    assert "up to date" in output.lower()
