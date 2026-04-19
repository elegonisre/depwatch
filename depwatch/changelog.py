"""Changelog summary: show what changed between two history snapshots."""
from __future__ import annotations
from dataclasses import dataclass
from typing import List, Dict
from depwatch.history import load_history


@dataclass
class ChangelogEntry:
    package: str
    project: str
    old_latest: str
    new_latest: str
    current_version: str
    was_outdated: bool
    is_outdated: bool


def _index_snapshot(records: list) -> Dict[str, dict]:
    """Key: 'project::package' -> record dict."""
    idx = {}
    for rec in records:
        key = f"{rec['project']}::{rec['package']}"
        idx[key] = rec
    return idx


def build_changelog(history_path: str, from_run: int = -2, to_run: int = -1) -> List[ChangelogEntry]:
    """Compare two runs from history and return changed entries."""
    runs = load_history(history_path)
    if len(runs) < 2:
        return []

    def _get_run(idx: int) -> list:
        return runs[idx].get("results", [])

    old_records = _get_run(from_run)
    new_records = _get_run(to_run)

    old_idx = _index_snapshot(old_records)
    new_idx = _index_snapshot(new_records)

    entries: List[ChangelogEntry] = []
    all_keys = set(old_idx) | set(new_idx)

    for key in sorted(all_keys):
        old = old_idx.get(key)
        new = new_idx.get(key)
        if old is None or new is None:
            continue
        if old["latest_version"] == new["latest_version"] and old["is_outdated"] == new["is_outdated"]:
            continue
        project, package = key.split("::", 1)
        entries.append(ChangelogEntry(
            package=package,
            project=project,
            old_latest=old["latest_version"],
            new_latest=new["latest_version"],
            current_version=new["current_version"],
            was_outdated=old["is_outdated"],
            is_outdated=new["is_outdated"],
        ))
    return entries


def format_changelog(entries: List[ChangelogEntry]) -> str:
    if not entries:
        return "No changes detected between the two runs."
    lines = ["Changelog (diff between last two runs):", ""]
    for e in entries:
        status = "outdated" if e.is_outdated else "up-to-date"
        lines.append(
            f"  [{e.project}] {e.package} {e.current_version}: "
            f"{e.old_latest} -> {e.new_latest}  ({status})"
        )
    return "\n".join(lines)
