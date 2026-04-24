"""Ownership tracking: assign owners (team/person) to packages per project."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Optional

DEFAULT_OWNERSHIP_FILE = Path(".depwatch_ownership.json")

# Structure: {project: {package: [owner, ...]}}
OwnershipMap = Dict[str, Dict[str, List[str]]]


def load_ownership(path: Path = DEFAULT_OWNERSHIP_FILE) -> OwnershipMap:
    """Load ownership map from JSON file. Returns empty dict if missing."""
    if not path.exists():
        return {}
    with path.open() as fh:
        return json.load(fh)


def save_ownership(data: OwnershipMap, path: Path = DEFAULT_OWNERSHIP_FILE) -> None:
    """Persist ownership map to JSON file."""
    with path.open("w") as fh:
        json.dump(data, fh, indent=2)


def assign_owner(
    data: OwnershipMap, project: str, package: str, owner: str
) -> OwnershipMap:
    """Assign *owner* to *package* in *project*. Idempotent."""
    data.setdefault(project, {}).setdefault(package, [])
    if owner not in data[project][package]:
        data[project][package].append(owner)
    return data


def remove_owner(
    data: OwnershipMap, project: str, package: str, owner: str
) -> OwnershipMap:
    """Remove *owner* from *package* in *project*. No-op if not present."""
    owners = data.get(project, {}).get(package, [])
    data.setdefault(project, {})[package] = [o for o in owners if o != owner]
    return data


def get_owners(
    data: OwnershipMap, project: str, package: str
) -> List[str]:
    """Return list of owners for *package* in *project*."""
    return data.get(project, {}).get(package, [])


def packages_for_owner(
    data: OwnershipMap, owner: str, project: Optional[str] = None
) -> Dict[str, List[str]]:
    """Return {project: [packages]} owned by *owner*, optionally filtered."""
    result: Dict[str, List[str]] = {}
    projects = [project] if project else list(data.keys())
    for proj in projects:
        pkgs = [
            pkg
            for pkg, owners in data.get(proj, {}).items()
            if owner in owners
        ]
        if pkgs:
            result[proj] = pkgs
    return result
