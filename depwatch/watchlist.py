"""Watchlist: mark specific packages for priority monitoring."""
from __future__ import annotations

import json
from pathlib import Path
from typing import List

from depwatch.checker import DependencyStatus

DEFAULT_WATCHLIST_FILE = Path(".depwatch_watchlist.json")


def load_watchlist(path: Path = DEFAULT_WATCHLIST_FILE) -> List[str]:
    """Return list of package names in the watchlist."""
    if not path.exists():
        return []
    return json.loads(path.read_text())


def save_watchlist(packages: List[str], path: Path = DEFAULT_WATCHLIST_FILE) -> None:
    """Persist the watchlist to disk."""
    path.write_text(json.dumps(sorted(set(packages)), indent=2))


def add_to_watchlist(package: str, path: Path = DEFAULT_WATCHLIST_FILE) -> List[str]:
    """Add a package to the watchlist (idempotent)."""
    packages = load_watchlist(path)
    if package not in packages:
        packages.append(package)
    save_watchlist(packages, path)
    return sorted(set(packages))


def remove_from_watchlist(package: str, path: Path = DEFAULT_WATCHLIST_FILE) -> List[str]:
    """Remove a package from the watchlist. No-op if not present."""
    packages = load_watchlist(path)
    packages = [p for p in packages if p != package]
    save_watchlist(packages, path)
    return packages


def filter_watchlist(
    statuses: List[DependencyStatus],
    path: Path = DEFAULT_WATCHLIST_FILE,
) -> List[DependencyStatus]:
    """Return only statuses whose package name is in the watchlist."""
    watched = set(load_watchlist(path))
    if not watched:
        return []
    return [s for s in statuses if s.package in watched]


def format_watchlist_report(statuses: List[DependencyStatus]) -> str:
    """Format a short report for watchlisted packages."""
    if not statuses:
        return "No watchlisted packages found in results."
    lines = ["Watchlisted packages:"]
    for s in statuses:
        flag = "[OUTDATED]" if s.is_outdated else "[ok]"
        lines.append(f"  {flag} {s.package} {s.current_version} -> {s.latest_version}")
    return "\n".join(lines)
