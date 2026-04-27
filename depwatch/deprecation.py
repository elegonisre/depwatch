"""Detect packages that are deprecated or have deprecation warnings on PyPI."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

import requests

from depwatch.checker import DependencyStatus


@dataclass
class DeprecationEntry:
    project: str
    package: str
    current_version: str
    deprecated: bool
    reason: Optional[str] = None
    successor: Optional[str] = None


def _fetch_pypi_info(package: str) -> dict:
    url = f"https://pypi.org/pypi/{package}/json"
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        return resp.json()
    except Exception:
        return {}


def _is_deprecated(info: dict) -> tuple[bool, Optional[str]]:
    """Return (deprecated, reason) by inspecting PyPI metadata."""
    if not info:
        return False, None
    meta = info.get("info", {})
    classifiers: List[str] = meta.get("classifiers", [])
    for clf in classifiers:
        if "Development Status" in clf and "Inactive" in clf:
            return True, "Development status: Inactive"
    description: str = (meta.get("description") or "").lower()
    for keyword in ("deprecated", "no longer maintained", "use instead", "replaced by"):
        if keyword in description:
            return True, f"Description contains '{keyword}'"
    return False, None


def _find_successor(info: dict) -> Optional[str]:
    """Attempt to extract a successor package name from PyPI metadata."""
    description: str = (info.get("info", {}).get("description") or "").lower()
    for phrase in ("use ", "replaced by ", "see "):
        idx = description.find(phrase)
        if idx != -1:
            rest = description[idx + len(phrase):].split()[0].strip(".,;:()'\"")
            if rest:
                return rest
    return None


def check_deprecations(
    statuses: List[DependencyStatus],
    project: str,
) -> List[DeprecationEntry]:
    """Check each dependency for deprecation signals on PyPI."""
    entries: List[DeprecationEntry] = []
    for status in statuses:
        info = _fetch_pypi_info(status.package)
        deprecated, reason = _is_deprecated(info)
        successor = _find_successor(info) if deprecated else None
        entries.append(
            DeprecationEntry(
                project=project,
                package=status.package,
                current_version=status.current_version,
                deprecated=deprecated,
                reason=reason,
                successor=successor,
            )
        )
    return entries


def format_deprecation_report(entries: List[DeprecationEntry]) -> str:
    """Render a human-readable deprecation report."""
    deprecated = [e for e in entries if e.deprecated]
    lines = [f"Deprecation Report — {len(deprecated)}/{len(entries)} deprecated"]
    lines.append("-" * 50)
    if not deprecated:
        lines.append("No deprecated packages found.")
    else:
        for e in deprecated:
            line = f"  {e.package} ({e.current_version})"
            if e.reason:
                line += f" — {e.reason}"
            if e.successor:
                line += f" → consider '{e.successor}'"
            lines.append(line)
    return "\n".join(lines)
