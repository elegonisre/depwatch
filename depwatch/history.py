"""Persistence layer for storing and retrieving dependency check history."""

from __future__ import annotations

import json
import os
from datetime import datetime
from typing import List, Dict, Any

from depwatch.checker import DependencyStatus

DEFAULT_HISTORY_FILE = ".depwatch_history.json"


def _status_to_dict(project: str, status: DependencyStatus, checked_at: str) -> Dict[str, Any]:
    return {
        "project": project,
        "package": status.package,
        "current_version": status.current_version,
        "latest_version": status.latest_version,
        "outdated": status.outdated,
        "checked_at": checked_at,
    }


def save_run(
    project: str,
    statuses: List[DependencyStatus],
    history_file: str = DEFAULT_HISTORY_FILE,
) -> None:
    """Append a check run to the history file."""
    checked_at = datetime.utcnow().isoformat()
    records = load_history(history_file)
    for status in statuses:
        records.append(_status_to_dict(project, status, checked_at))
    with open(history_file, "w", encoding="utf-8") as fh:
        json.dump(records, fh, indent=2)


def load_history(history_file: str = DEFAULT_HISTORY_FILE) -> List[Dict[str, Any]]:
    """Load all historical records from the history file."""
    if not os.path.exists(history_file):
        return []
    with open(history_file, "r", encoding="utf-8") as fh:
        return json.load(fh)


def get_project_history(
    project: str, history_file: str = DEFAULT_HISTORY_FILE
) -> List[Dict[str, Any]]:
    """Return records filtered to a specific project."""
    return [r for r in load_history(history_file) if r["project"] == project]


def clear_history(history_file: str = DEFAULT_HISTORY_FILE) -> None:
    """Delete all history records."""
    if os.path.exists(history_file):
        os.remove(history_file)
