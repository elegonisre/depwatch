"""Group dependency statuses by various attributes."""
from __future__ import annotations
from collections import defaultdict
from typing import Dict, List
from depwatch.checker import DependencyStatus


def group_by_project(statuses: List[DependencyStatus]) -> Dict[str, List[DependencyStatus]]:
    """Group statuses by project name."""
    groups: Dict[str, List[DependencyStatus]] = defaultdict(list)
    for s in statuses:
        groups[s.project].append(s)
    return dict(groups)


def group_by_status(statuses: List[DependencyStatus]) -> Dict[str, List[DependencyStatus]]:
    """Group statuses into 'outdated' and 'up_to_date' buckets."""
    groups: Dict[str, List[DependencyStatus]] = {"outdated": [], "up_to_date": []}
    for s in statuses:
        key = "outdated" if s.is_outdated else "up_to_date"
        groups[key].append(s)
    return groups


def group_by_major_version_gap(statuses: List[DependencyStatus]) -> Dict[str, List[DependencyStatus]]:
    """Group outdated statuses by major version gap (0, 1, 2+)."""
    groups: Dict[str, List[DependencyStatus]] = {"none": [], "one": [], "multiple": []}
    for s in statuses:
        if not s.is_outdated or not s.latest_version or not s.current_version:
            groups["none"].append(s)
            continue
        try:
            cur_major = int(s.current_version.split(".")[0])
            lat_major = int(s.latest_version.split(".")[0])
            gap = lat_major - cur_major
        except (ValueError, IndexError):
            groups["none"].append(s)
            continue
        if gap == 0:
            groups["none"].append(s)
        elif gap == 1:
            groups["one"].append(s)
        else:
            groups["multiple"].append(s)
    return groups


def summary(statuses: List[DependencyStatus]) -> Dict[str, int]:
    """Return a count summary across all statuses."""
    total = len(statuses)
    outdated = sum(1 for s in statuses if s.is_outdated)
    return {"total": total, "outdated": outdated, "up_to_date": total - outdated}
