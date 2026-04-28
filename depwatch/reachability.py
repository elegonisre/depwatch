"""Reachability analysis: detect packages that are no longer importable or
have been yanked on PyPI."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

import requests

from depwatch.checker import DependencyStatus


@dataclass
class ReachabilityEntry:
    project: str
    package: str
    current_version: str
    yanked: bool
    yanked_reason: str | None = None
    error: str | None = None


def _fetch_version_info(package: str, version: str) -> dict:
    """Return the PyPI release info dict for *package*==*version*."""
    url = f"https://pypi.org/pypi/{package}/{version}/json"
    resp = requests.get(url, timeout=10)
    resp.raise_for_status()
    return resp.json()


def check_reachability(status: DependencyStatus) -> ReachabilityEntry:
    """Check whether the currently installed version of a dependency has been
    yanked on PyPI."""
    try:
        data = _fetch_version_info(status.package_name, status.current_version)
        urls: list = data.get("urls", [])
        if not urls:
            # Fall back to info block
            info = data.get("info", {})
            yanked = bool(info.get("yanked", False))
            yanked_reason = info.get("yanked_reason") or None
        else:
            yanked = any(u.get("yanked", False) for u in urls)
            reasons = [u.get("yanked_reason") for u in urls if u.get("yanked_reason")]
            yanked_reason = reasons[0] if reasons else None
        return ReachabilityEntry(
            project=status.project_name,
            package=status.package_name,
            current_version=status.current_version,
            yanked=yanked,
            yanked_reason=yanked_reason,
        )
    except Exception as exc:  # noqa: BLE001
        return ReachabilityEntry(
            project=status.project_name,
            package=status.package_name,
            current_version=status.current_version,
            yanked=False,
            error=str(exc),
        )


def check_all_reachability(
    statuses: List[DependencyStatus],
) -> List[ReachabilityEntry]:
    """Run reachability checks for every status entry."""
    return [check_reachability(s) for s in statuses]


def format_reachability_report(entries: List[ReachabilityEntry]) -> str:
    yanked = [e for e in entries if e.yanked]
    errors = [e for e in entries if e.error]
    lines: list[str] = ["=== Reachability Report ==="]
    if not yanked and not errors:
        lines.append("All checked versions are reachable.")
        return "\n".join(lines)
    if yanked:
        lines.append(f"\nYanked packages ({len(yanked)}):")
        for e in yanked:
            reason = f" — {e.yanked_reason}" if e.yanked_reason else ""
            lines.append(f"  [{e.project}] {e.package}=={e.current_version}{reason}")
    if errors:
        lines.append(f"\nCheck errors ({len(errors)}):")
        for e in errors:
            lines.append(f"  [{e.project}] {e.package}: {e.error}")
    return "\n".join(lines)
