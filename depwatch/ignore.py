"""Manage a persistent ignore list for dependencies."""
from __future__ import annotations

import json
from pathlib import Path
from typing import List

DEFAULT_IGNORE_FILE = Path(".depwatch_ignore.json")


def load_ignore_list(path: Path = DEFAULT_IGNORE_FILE) -> List[str]:
    """Load ignored package names from a JSON file."""
    if not path.exists():
        return []
    with path.open() as f:
        data = json.load(f)
    return list(data.get("ignore", []))


def save_ignore_list(packages: List[str], path: Path = DEFAULT_IGNORE_FILE) -> None:
    """Persist ignored package names to a JSON file."""
    unique = sorted(set(packages))
    with path.open("w") as f:
        json.dump({"ignore": unique}, f, indent=2)


def add_to_ignore(package: str, path: Path = DEFAULT_IGNORE_FILE) -> List[str]:
    """Add a package to the ignore list and save."""
    current = load_ignore_list(path)
    if package not in current:
        current.append(package)
    save_ignore_list(current, path)
    return sorted(set(current))


def remove_from_ignore(package: str, path: Path = DEFAULT_IGNORE_FILE) -> List[str]:
    """Remove a package from the ignore list and save."""
    current = load_ignore_list(path)
    updated = [p for p in current if p != package]
    save_ignore_list(updated, path)
    return updated
