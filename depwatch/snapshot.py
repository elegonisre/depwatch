"""Snapshot diffing: compare two runs to highlight changes in dependency status."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional

from depwatch.checker import DependencyStatus


@dataclass
class DiffEntry:
    package: str
    old_status: Optional[str]  # 'outdated', 'up-to-date', or None if new
    new_status: str
    old_version: Optional[str]
    new_version: Optional[str]
    latest_version: str


@dataclass
class SnapshotDiff:
    project: str
    new_outdated: List[DiffEntry]
    resolved: List[DiffEntry]
    changed_version: List[DiffEntry]
    unchanged: List[DiffEntry]

    @property
    def has_changes(self) -> bool:
        return bool(self.new_outdated or self.resolved or self.changed_version)


def _index(statuses: List[DependencyStatus]) -> Dict[str, DependencyStatus]:
    return {s.package: s for s in statuses}


def diff_snapshots(
    project: str,
    previous: List[DependencyStatus],
    current: List[DependencyStatus],
) -> SnapshotDiff:
    """Compare two lists of DependencyStatus for the same project."""
    prev_idx = _index(previous)
    curr_idx = _index(current)

    new_outdated: List[DiffEntry] = []
    resolved: List[DiffEntry] = []
    changed_version: List[DiffEntry] = []
    unchanged: List[DiffEntry] = []

    all_packages = set(prev_idx) | set(curr_idx)

    for pkg in sorted(all_packages):
        curr = curr_idx.get(pkg)
        prev = prev_idx.get(pkg)

        if curr is None:
            continue  # package removed — skip

        entry = DiffEntry(
            package=pkg,
            old_status="outdated" if (prev and prev.outdated) else ("up-to-date" if prev else None),
            new_status="outdated" if curr.outdated else "up-to-date",
            old_version=prev.current_version if prev else None,
            new_version=curr.current_version,
            latest_version=curr.latest_version,
        )

        if prev is None or (not prev.outdated and curr.outdated):
            new_outdated.append(entry)
        elif prev.outdated and not curr.outdated:
            resolved.append(entry)
        elif prev.outdated and curr.outdated and prev.current_version != curr.current_version:
            changed_version.append(entry)
        else:
            unchanged.append(entry)

    return SnapshotDiff(
        project=project,
        new_outdated=new_outdated,
        resolved=resolved,
        changed_version=changed_version,
        unchanged=unchanged,
    )
