"""Tests for depwatch.suppress."""
from __future__ import annotations

import json
from datetime import datetime, timezone, timedelta
from pathlib import Path
from unittest.mock import patch

import pytest

from depwatch.suppress import (
    suppress_package,
    remove_suppression,
    is_suppressed,
    list_suppressions,
    load_suppressions,
)


@pytest.fixture
def sf(tmp_path):
    return tmp_path / "suppress.json"


def _future(days=7):
    return datetime.now(timezone.utc) + timedelta(days=days)


def _past(days=1):
    return datetime.now(timezone.utc) - timedelta(days=days)


def test_load_missing_file(sf):
    assert load_suppressions(sf) == {}


def test_suppress_and_load(sf):
    suppress_package("requests", _future(), "waiting for fix", path=sf)
    data = load_suppressions(sf)
    assert "requests" in data
    assert data["requests"]["reason"] == "waiting for fix"


def test_is_suppressed_active(sf):
    suppress_package("flask", _future(3), path=sf)
    assert is_suppressed("flask", path=sf) is True


def test_is_suppressed_expired(sf):
    suppress_package("flask", _past(1), path=sf)
    assert is_suppressed("flask", path=sf) is False


def test_is_suppressed_unknown(sf):
    assert is_suppressed("nonexistent", path=sf) is False


def test_remove_existing(sf):
    suppress_package("django", _future(), path=sf)
    result = remove_suppression("django", path=sf)
    assert result is True
    assert "django" not in load_suppressions(sf)


def test_remove_nonexistent(sf):
    result = remove_suppression("ghost", path=sf)
    assert result is False


def test_list_suppressions(sf):
    suppress_package("a", _future(5), "reason a", path=sf)
    suppress_package("b", _past(1), path=sf)
    entries = list_suppressions(sf)
    by_pkg = {e["package"]: e for e in entries}
    assert by_pkg["a"]["active"] is True
    assert by_pkg["b"]["active"] is False
    assert by_pkg["a"]["reason"] == "reason a"
