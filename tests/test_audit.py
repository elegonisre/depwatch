"""Tests for depwatch.audit."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from depwatch.audit import (
    AuditEntry,
    format_audit_log,
    load_audit_log,
    record_audit,
)


@pytest.fixture()
def af(tmp_path: Path) -> Path:
    return tmp_path / "audit.jsonl"


def test_load_missing_file_returns_empty(af: Path):
    assert load_audit_log(af) == []


def test_record_creates_file(af: Path):
    record_audit("myproject", total=5, outdated=2, audit_file=af)
    assert af.exists()


def test_record_and_load_roundtrip(af: Path):
    record_audit("proj", total=10, outdated=3, triggered_by="scheduler", tags=["ci"], note="weekly", audit_file=af)
    entries = load_audit_log(af)
    assert len(entries) == 1
    e = entries[0]
    assert e.project == "proj"
    assert e.total == 10
    assert e.outdated == 3
    assert e.triggered_by == "scheduler"
    assert e.tags == ["ci"]
    assert e.note == "weekly"


def test_record_appends_multiple(af: Path):
    record_audit("a", total=2, outdated=1, audit_file=af)
    record_audit("b", total=4, outdated=0, audit_file=af)
    entries = load_audit_log(af)
    assert len(entries) == 2
    assert entries[0].project == "a"
    assert entries[1].project == "b"


def test_record_returns_entry(af: Path):
    e = record_audit("x", total=1, outdated=1, audit_file=af)
    assert isinstance(e, AuditEntry)
    assert e.project == "x"


def test_format_empty():
    result = format_audit_log([])
    assert "No audit records" in result


def test_format_shows_project(af: Path):
    record_audit("myapp", total=8, outdated=2, audit_file=af)
    entries = load_audit_log(af)
    report = format_audit_log(entries)
    assert "myapp" in report
    assert "8" in report
    assert "2" in report


def test_format_shows_tags(af: Path):
    record_audit("tagtest", total=3, outdated=1, tags=["prod", "release"], audit_file=af)
    entries = load_audit_log(af)
    report = format_audit_log(entries)
    assert "prod" in report
    assert "release" in report
