"""Tests for depwatch.badge."""
import pytest
from depwatch.checker import DependencyStatus
from depwatch.badge import (
    build_badge,
    badge_to_shields_url,
    get_badge_color,
    BadgeData,
)


def _s(name: str, current: str, latest: str) -> DependencyStatus:
    return DependencyStatus(
        name=name,
        current_version=current,
        latest_version=latest,
        is_outdated=current != latest,
    )


def test_get_badge_color_all_up_to_date():
    assert get_badge_color(0, 5) == "brightgreen"


def test_get_badge_color_no_deps():
    assert get_badge_color(0, 0) == "lightgrey"


def test_get_badge_color_low_ratio():
    assert get_badge_color(1, 10) == "yellow"


def test_get_badge_color_mid_ratio():
    assert get_badge_color(3, 6) == "orange"


def test_get_badge_color_high_ratio():
    assert get_badge_color(5, 6) == "red"


def test_build_badge_all_up_to_date():
    statuses = [_s("requests", "2.28.0", "2.28.0"), _s("flask", "2.0.0", "2.0.0")]
    badge = build_badge("myproject", statuses)
    assert badge.label == "myproject"
    assert badge.message == "0/2 outdated"
    assert badge.color == "brightgreen"


def test_build_badge_some_outdated():
    statuses = [_s("requests", "2.27.0", "2.28.0"), _s("flask", "2.0.0", "2.0.0")]
    badge = build_badge("myproject", statuses)
    assert badge.message == "1/2 outdated"
    assert badge.color == "yellow"


def test_build_badge_no_deps():
    badge = build_badge("empty", [])
    assert badge.message == "no deps"
    assert badge.color == "lightgrey"


def test_badge_to_shields_url_contains_parts():
    badge = BadgeData(label="myproject", message="0/3 outdated", color="brightgreen")
    url = badge_to_shields_url(badge)
    assert "img.shields.io/badge/" in url
    assert "brightgreen" in url
    assert "myproject" in url


def test_badge_to_shields_url_encodes_spaces():
    badge = BadgeData(label="my project", message="1/5 outdated", color="yellow")
    url = badge_to_shields_url(badge)
    assert " " not in url
