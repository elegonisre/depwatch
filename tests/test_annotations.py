"""Tests for depwatch.annotations."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from depwatch.annotations import (
    add_annotation,
    clear_annotations,
    get_annotations,
    list_all_annotations,
    load_annotations,
    remove_annotation,
)


@pytest.fixture()
def af(tmp_path: Path) -> Path:
    return tmp_path / "annotations.json"


def test_load_missing_file_returns_empty(af: Path) -> None:
    result = load_annotations(af)
    assert result == {}


def test_add_new_annotation(af: Path) -> None:
    notes = add_annotation("myproject", "requests", "pinned for compat", path=af)
    assert notes == ["pinned for compat"]
    assert af.exists()


def test_add_duplicate_is_idempotent(af: Path) -> None:
    add_annotation("myproject", "requests", "note", path=af)
    notes = add_annotation("myproject", "requests", "note", path=af)
    assert notes.count("note") == 1


def test_add_multiple_notes(af: Path) -> None:
    add_annotation("myproject", "django", "first", path=af)
    notes = add_annotation("myproject", "django", "second", path=af)
    assert notes == ["first", "second"]


def test_get_annotations_returns_notes(af: Path) -> None:
    add_annotation("proj", "flask", "upgrade soon", path=af)
    result = get_annotations("proj", "flask", path=af)
    assert result == ["upgrade soon"]


def test_get_annotations_missing_returns_empty(af: Path) -> None:
    result = get_annotations("proj", "nonexistent", path=af)
    assert result == []


def test_remove_annotation(af: Path) -> None:
    add_annotation("proj", "numpy", "keep", path=af)
    add_annotation("proj", "numpy", "remove me", path=af)
    remaining = remove_annotation("proj", "numpy", "remove me", path=af)
    assert "remove me" not in remaining
    assert "keep" in remaining


def test_remove_last_annotation_cleans_key(af: Path) -> None:
    add_annotation("proj", "scipy", "only note", path=af)
    remove_annotation("proj", "scipy", "only note", path=af)
    data = load_annotations(af)
    assert "proj/scipy" not in data


def test_list_all_annotations(af: Path) -> None:
    add_annotation("a", "pkg1", "note1", path=af)
    add_annotation("b", "pkg2", "note2", path=af)
    all_data = list_all_annotations(af)
    assert "a/pkg1" in all_data
    assert "b/pkg2" in all_data


def test_clear_annotations_for_project(af: Path) -> None:
    add_annotation("proj1", "pkg", "note", path=af)
    add_annotation("proj2", "pkg", "note", path=af)
    clear_annotations(project="proj1", path=af)
    data = load_annotations(af)
    assert "proj1/pkg" not in data
    assert "proj2/pkg" in data


def test_clear_all_annotations(af: Path) -> None:
    add_annotation("proj1", "pkg", "note", path=af)
    add_annotation("proj2", "pkg", "note", path=af)
    clear_annotations(path=af)
    assert load_annotations(af) == {}
