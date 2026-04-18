"""Tests for depwatch.pin."""
import pytest
from depwatch.checker import DependencyStatus
from depwatch.pin import suggest_pins, format_suggestions, PinSuggestion


def _s(package, current, latest, is_outdated, project="proj"):
    return DependencyStatus(
        project=project,
        package=package,
        current_version=current,
        latest_version=latest,
        is_outdated=is_outdated,
    )


def test_suggest_pins_outdated():
    statuses = [_s("django", "3.2", "4.2", True)]
    suggestions = suggest_pins(statuses)
    assert len(suggestions) == 1
    s = suggestions[0]
    assert s.action == "upgrade"
    assert s.pin_spec == "django==4.2"
    assert s.package == "django"


def test_suggest_pins_up_to_date_no_pin_by_default():
    statuses = [_s("requests", "2.31", "2.31", False)]
    suggestions = suggest_pins(statuses)
    assert suggestions == []


def test_suggest_pins_pin_current_flag():
    statuses = [_s("requests", "2.31", "2.31", False)]
    suggestions = suggest_pins(statuses, pin_to_latest=True)
    assert len(suggestions) == 1
    assert suggestions[0].action == "pin"
    assert suggestions[0].pin_spec == "requests==2.31"


def test_suggest_pins_already_pinned_skipped():
    # current_version contains '==' — should not re-pin
    statuses = [_s("flask", "==2.0", "2.0", False)]
    suggestions = suggest_pins(statuses, pin_to_latest=True)
    assert suggestions == []


def test_format_suggestions_empty():
    assert format_suggestions([]) == "No pin/upgrade suggestions."


def test_format_suggestions_contains_package():
    suggestions = [
        PinSuggestion(project="p", package="django", current="3.2", latest="4.2", action="upgrade", pin_spec="django==4.2")
    ]
    out = format_suggestions(suggestions)
    assert "django==4.2" in out
    assert "UPGRADE" in out
    assert "3.2" in out


def test_suggest_pins_multiple_projects():
    statuses = [
        _s("a", "1.0", "2.0", True, project="alpha"),
        _s("b", "3.0", "3.0", False, project="beta"),
        _s("c", "0.1", "1.0", True, project="beta"),
    ]
    suggestions = suggest_pins(statuses)
    assert len(suggestions) == 2
    packages = {s.package for s in suggestions}
    assert packages == {"a", "c"}
