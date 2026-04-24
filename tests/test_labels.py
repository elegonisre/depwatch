"""Tests for depwatch.labels."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from depwatch.labels import (
    add_label,
    filter_by_label,
    get_labels,
    load_labels,
    remove_label,
    save_labels,
)


@pytest.fixture()
def lf(tmp_path: Path) -> Path:
    return tmp_path / "labels.json"


def test_load_missing_file_returns_empty(lf: Path) -> None:
    assert load_labels(lf) == {}


def test_save_and_load_roundtrip(lf: Path) -> None:
    data = {"requests": ["critical", "network"], "flask": ["web"]}
    save_labels(data, lf)
    assert load_labels(lf) == data


def test_add_new_label(lf: Path) -> None:
    add_label("django", "web", lf)
    assert "web" in get_labels("django", lf)


def test_add_duplicate_is_idempotent(lf: Path) -> None:
    add_label("django", "web", lf)
    add_label("django", "web", lf)
    assert get_labels("django", lf).count("web") == 1


def test_add_multiple_labels(lf: Path) -> None:
    add_label("requests", "network", lf)
    add_label("requests", "critical", lf)
    labels = get_labels("requests", lf)
    assert "network" in labels
    assert "critical" in labels


def test_remove_existing_label(lf: Path) -> None:
    add_label("flask", "web", lf)
    remove_label("flask", "web", lf)
    assert get_labels("flask", lf) == []


def test_remove_last_label_cleans_key(lf: Path) -> None:
    add_label("flask", "web", lf)
    remove_label("flask", "web", lf)
    assert "flask" not in load_labels(lf)


def test_remove_missing_label_is_noop(lf: Path) -> None:
    add_label("flask", "web", lf)
    remove_label("flask", "nonexistent", lf)  # should not raise
    assert get_labels("flask", lf) == ["web"]


def test_get_labels_unknown_package(lf: Path) -> None:
    assert get_labels("unknown", lf) == []


def test_filter_by_label_returns_matching(lf: Path) -> None:
    add_label("requests", "network", lf)
    add_label("urllib3", "network", lf)
    add_label("flask", "web", lf)
    result = filter_by_label(["requests", "urllib3", "flask"], "network", lf)
    assert result == ["requests", "urllib3"]


def test_filter_by_label_no_match(lf: Path) -> None:
    add_label("flask", "web", lf)
    result = filter_by_label(["flask"], "network", lf)
    assert result == []
