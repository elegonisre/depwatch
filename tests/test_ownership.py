"""Tests for depwatch.ownership module."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from depwatch.ownership import (
    assign_owner,
    get_owners,
    load_ownership,
    packages_for_owner,
    remove_owner,
    save_ownership,
)


@pytest.fixture()
def of(tmp_path: Path) -> Path:
    return tmp_path / "ownership.json"


def test_load_missing_file_returns_empty(of: Path) -> None:
    assert load_ownership(of) == {}


def test_save_and_load_roundtrip(of: Path) -> None:
    data = {"proj": {"requests": ["alice"]}}
    save_ownership(data, of)
    assert load_ownership(of) == data


def test_assign_owner_new_project(of: Path) -> None:
    data = load_ownership(of)
    assign_owner(data, "proj", "requests", "alice")
    assert "alice" in data["proj"]["requests"]


def test_assign_owner_idempotent() -> None:
    data: dict = {}
    assign_owner(data, "proj", "requests", "alice")
    assign_owner(data, "proj", "requests", "alice")
    assert data["proj"]["requests"].count("alice") == 1


def test_assign_multiple_owners() -> None:
    data: dict = {}
    assign_owner(data, "proj", "django", "alice")
    assign_owner(data, "proj", "django", "bob")
    assert set(data["proj"]["django"]) == {"alice", "bob"}


def test_remove_owner_existing() -> None:
    data: dict = {"proj": {"requests": ["alice", "bob"]}}
    remove_owner(data, "proj", "requests", "alice")
    assert "alice" not in data["proj"]["requests"]
    assert "bob" in data["proj"]["requests"]


def test_remove_owner_missing_is_noop() -> None:
    data: dict = {"proj": {"requests": ["bob"]}}
    remove_owner(data, "proj", "requests", "alice")  # should not raise
    assert data["proj"]["requests"] == ["bob"]


def test_get_owners_returns_list() -> None:
    data = {"proj": {"flask": ["carol"]}}
    assert get_owners(data, "proj", "flask") == ["carol"]


def test_get_owners_unknown_package() -> None:
    assert get_owners({}, "proj", "unknown") == []


def test_packages_for_owner_all_projects() -> None:
    data = {
        "proj_a": {"requests": ["alice"], "flask": ["bob"]},
        "proj_b": {"django": ["alice"]},
    }
    result = packages_for_owner(data, "alice")
    assert result == {"proj_a": ["requests"], "proj_b": ["django"]}


def test_packages_for_owner_filtered_project() -> None:
    data = {
        "proj_a": {"requests": ["alice"]},
        "proj_b": {"django": ["alice"]},
    }
    result = packages_for_owner(data, "alice", project="proj_a")
    assert "proj_b" not in result
    assert result["proj_a"] == ["requests"]


def test_packages_for_owner_none_found() -> None:
    data = {"proj": {"requests": ["bob"]}}
    assert packages_for_owner(data, "alice") == {}
