"""Temporary suppression of outdated alerts for specific packages."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

DEFAULT_SUPPRESS_FILE = Path(".depwatch_suppress.json")


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def load_suppressions(path: Path = DEFAULT_SUPPRESS_FILE) -> dict:
    if not path.exists():
        return {}
    return json.loads(path.read_text())


def save_suppressions(data: dict, path: Path = DEFAULT_SUPPRESS_FILE) -> None:
    path.write_text(json.dumps(data, indent=2))


def suppress_package(
    package: str,
    until: datetime,
    reason: str = "",
    path: Path = DEFAULT_SUPPRESS_FILE,
) -> None:
    data = load_suppressions(path)
    data[package] = {
        "until": until.isoformat(),
        "reason": reason,
    }
    save_suppressions(data, path)


def remove_suppression(package: str, path: Path = DEFAULT_SUPPRESS_FILE) -> bool:
    data = load_suppressions(path)
    if package not in data:
        return False
    del data[package]
    save_suppressions(data, path)
    return True


def is_suppressed(package: str, path: Path = DEFAULT_SUPPRESS_FILE) -> bool:
    data = load_suppressions(path)
    if package not in data:
        return False
    until = datetime.fromisoformat(data[package]["until"])
    return _utcnow() < until


def list_suppressions(path: Path = DEFAULT_SUPPRESS_FILE) -> list[dict]:
    data = load_suppressions(path)
    now = _utcnow()
    result = []
    for pkg, info in data.items():
        until = datetime.fromisoformat(info["until"])
        result.append({
            "package": pkg,
            "until": until,
            "reason": info.get("reason", ""),
            "active": now < until,
        })
    return result
