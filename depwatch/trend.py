"""Analyse history records to surface dependency trends."""

from __future__ import annotations

from collections import defaultdict
from typing import Dict, List, Any


def outdated_counts_over_time(
    records: List[Dict[str, Any]]
) -> Dict[str, int]:
    """Return a mapping of checked_at timestamp -> number of outdated packages."""
    counts: Dict[str, int] = defaultdict(int)
    for record in records:
        if record.get("outdated"):
            counts[record["checked_at"]] += 1
    return dict(counts)


def most_frequently_outdated(
    records: List[Dict[str, Any]], top_n: int = 5
) -> List[Dict[str, Any]]:
    """Return the top N packages most often found outdated."""
    freq: Dict[str, int] = defaultdict(int)
    for record in records:
        if record.get("outdated"):
            freq[record["package"]] += 1
    sorted_packages = sorted(freq.items(), key=lambda x: x[1], reverse=True)
    return [{"package": pkg, "outdated_count": cnt} for pkg, cnt in sorted_packages[:top_n]]


def latest_snapshot(
    records: List[Dict[str, Any]], project: str
) -> List[Dict[str, Any]]:
    """Return the most recent check record per package for a project."""
    latest: Dict[str, Dict[str, Any]] = {}
    for record in records:
        if record.get("project") != project:
            continue
        pkg = record["package"]
        if pkg not in latest or record["checked_at"] > latest[pkg]["checked_at"]:
            latest[pkg] = record
    return list(latest.values())
