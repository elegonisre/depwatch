"""Filtering utilities for dependency check results."""
from __future__ import annotations
from typing import List, Optional
from depwatch.checker import DependencyStatus


def filter_outdated(statuses: List[DependencyStatus]) -> List[DependencyStatus]:
    """Return only outdated dependencies."""
    return [s for s in statuses if s.is_outdated]


def filter_by_name(statuses: List[DependencyStatus], names: List[str]) -> List[DependencyStatus]:
    """Return only dependencies whose names are in *names* (case-insensitive)."""
    lower = {n.lower() for n in names}
    return [s for s in statuses if s.name.lower() in lower]


def filter_by_project(records: List[dict], project: str) -> List[dict]:
    """Filter history records to a single project name (case-insensitive)."""
    return [r for r in records if r.get("project", "").lower() == project.lower()]


def filter_min_versions_behind(
    statuses: List[DependencyStatus],
    min_behind: int,
) -> List[DependencyStatus]:
    """Return outdated deps where the major version component is at least *min_behind* behind.

    Falls back to including the dep if versions cannot be parsed.
    """
    result = []
    for s in statuses:
        if not s.is_outdated:
            continue
        try:
            current_major = int(s.current_version.split(".")[0])
            latest_major = int(s.latest_version.split(".")[0])
            if latest_major - current_major >= min_behind:
                result.append(s)
        except (ValueError, AttributeError):
            result.append(s)
    return result


def apply_ignore_list(
    statuses: List[DependencyStatus],
    ignore: Optional[List[str]],
) -> List[DependencyStatus]:
    """Remove any dependency whose name appears in *ignore*."""
    if not ignore:
        return statuses
    lower = {n.lower() for n in ignore}
    return [s for s in statuses if s.name.lower() not in lower]
