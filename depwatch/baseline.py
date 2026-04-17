"""Baseline management: pin current dependency state as a reference point."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from depwatch.checker import DependencyStatus

DEFAULT_BASELINE_FILE = Path(".depwatch_baseline.json")


def _status_to_dict(s: DependencyStatus) -> dict:
    return {
        "package": s.package,
        "current": s.current_version,
        "latest": s.latest_version,
        "outdated": s.outdated,
    }


def save_baseline(
    project: str,
    statuses: list[DependencyStatus],
    path: Path = DEFAULT_BASELINE_FILE,
) -> None:
    """Persist current statuses as the baseline for a project."""
    data: dict = {}
    if path.exists():
        data = json.loads(path.read_text())
    data[project] = {
        "saved_at": datetime.now(timezone.utc).isoformat(),
        "packages": [_status_to_dict(s) for s in statuses],
    }
    path.write_text(json.dumps(data, indent=2))


def load_baseline(
    project: str,
    path: Path = DEFAULT_BASELINE_FILE,
) -> Optional[list[dict]]:
    """Return baseline package list for *project*, or None if absent."""
    if not path.exists():
        return None
    data = json.loads(path.read_text())
    entry = data.get(project)
    if entry is None:
        return None
    return entry["packages"]


def diff_from_baseline(
    project: str,
    current: list[DependencyStatus],
    path: Path = DEFAULT_BASELINE_FILE,
) -> dict[str, list[str]]:
    """Compare *current* statuses against saved baseline.

    Returns dict with keys 'new_outdated', 'resolved', 'version_changed'.
    """
    baseline = load_baseline(project, path)
    if baseline is None:
        return {"new_outdated": [], "resolved": [], "version_changed": []}

    base_index = {p["package"]: p for p in baseline}
    cur_index = {s.package: s for s in current}

    new_outdated, resolved, version_changed = [], [], []

    for pkg, cur in cur_index.items():
        base = base_index.get(pkg)
        if base is None:
            if cur.outdated:
                new_outdated.append(pkg)
            continue
        was_outdated = base["outdated"]
        if cur.outdated and not was_outdated:
            new_outdated.append(pkg)
        elif not cur.outdated and was_outdated:
            resolved.append(pkg)
        elif cur.outdated and was_outdated and cur.latest_version != base["latest"]:
            version_changed.append(pkg)

    return {"new_outdated": new_outdated, "resolved": resolved, "version_changed": version_changed}
