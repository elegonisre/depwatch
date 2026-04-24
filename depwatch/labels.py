"""Dependency label management — attach custom tags to packages for grouping and filtering."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List

DEFAULT_LABELS_FILE = Path(".depwatch_labels.json")


def load_labels(path: Path = DEFAULT_LABELS_FILE) -> Dict[str, List[str]]:
    """Return mapping of package -> list[label]. Empty dict if file missing."""
    if not path.exists():
        return {}
    with path.open() as fh:
        return json.load(fh)


def save_labels(labels: Dict[str, List[str]], path: Path = DEFAULT_LABELS_FILE) -> None:
    """Persist labels mapping to *path*."""
    with path.open("w") as fh:
        json.dump(labels, fh, indent=2)


def add_label(package: str, label: str, path: Path = DEFAULT_LABELS_FILE) -> None:
    """Attach *label* to *package*. Idempotent."""
    labels = load_labels(path)
    existing = labels.setdefault(package, [])
    if label not in existing:
        existing.append(label)
    save_labels(labels, path)


def remove_label(package: str, label: str, path: Path = DEFAULT_LABELS_FILE) -> None:
    """Remove *label* from *package*. No-op if absent."""
    labels = load_labels(path)
    if package in labels:
        labels[package] = [l for l in labels[package] if l != label]
        if not labels[package]:
            del labels[package]
    save_labels(labels, path)


def get_labels(package: str, path: Path = DEFAULT_LABELS_FILE) -> List[str]:
    """Return labels for *package*, or empty list."""
    return load_labels(path).get(package, [])


def filter_by_label(
    packages: List[str], label: str, path: Path = DEFAULT_LABELS_FILE
) -> List[str]:
    """Return only those *packages* that carry *label*."""
    labels = load_labels(path)
    return [p for p in packages if label in labels.get(p, [])]
