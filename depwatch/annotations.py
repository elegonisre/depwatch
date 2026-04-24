"""Annotations: attach free-text notes to packages across projects."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Optional

_DEFAULT_PATH = Path(".depwatch_annotations.json")

# Storage format: {"<project>/<package>": ["note1", "note2", ...]}


def _key(project: str, package: str) -> str:
    return f"{project}/{package}"


def load_annotations(path: Path = _DEFAULT_PATH) -> Dict[str, List[str]]:
    """Load annotations from *path*. Returns empty dict if file is missing."""
    if not path.exists():
        return {}
    return json.loads(path.read_text())


def save_annotations(data: Dict[str, List[str]], path: Path = _DEFAULT_PATH) -> None:
    """Persist annotations to *path*."""
    path.write_text(json.dumps(data, indent=2))


def add_annotation(
    project: str,
    package: str,
    note: str,
    path: Path = _DEFAULT_PATH,
) -> List[str]:
    """Append *note* for *package* in *project*. Returns updated note list."""
    data = load_annotations(path)
    k = _key(project, package)
    notes = data.setdefault(k, [])
    if note not in notes:
        notes.append(note)
    save_annotations(data, path)
    return notes


def remove_annotation(
    project: str,
    package: str,
    note: str,
    path: Path = _DEFAULT_PATH,
) -> List[str]:
    """Remove *note* for *package* in *project*. Returns updated note list."""
    data = load_annotations(path)
    k = _key(project, package)
    notes = data.get(k, [])
    data[k] = [n for n in notes if n != note]
    if not data[k]:
        del data[k]
    save_annotations(data, path)
    return data.get(k, [])


def get_annotations(
    project: str,
    package: str,
    path: Path = _DEFAULT_PATH,
) -> List[str]:
    """Return all notes for *package* in *project*."""
    data = load_annotations(path)
    return data.get(_key(project, package), [])


def list_all_annotations(
    path: Path = _DEFAULT_PATH,
) -> Dict[str, List[str]]:
    """Return all annotations keyed by 'project/package'."""
    return load_annotations(path)


def clear_annotations(
    project: Optional[str] = None,
    path: Path = _DEFAULT_PATH,
) -> None:
    """Clear annotations for *project*, or all annotations if project is None."""
    if project is None:
        save_annotations({}, path)
        return
    data = load_annotations(path)
    prefix = f"{project}/"
    data = {k: v for k, v in data.items() if not k.startswith(prefix)}
    save_annotations(data, path)
