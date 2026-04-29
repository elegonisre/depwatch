"""Pinning status: check whether installed versions match pinned requirements."""
from __future__ import annotations

from dataclasses import dataclass
from typing import List

from depwatch.checker import DependencyStatus


@dataclass
class PinningEntry:
    project: str
    package: str
    current_version: str
    latest_version: str
    is_pinned: bool          # version looks like an exact pin (no specifier wildcards)
    is_outdated: bool
    pin_matches_latest: bool  # pinned AND already at latest


def _looks_pinned(version: str) -> bool:
    """Return True when the version string is a plain exact version (no specifiers)."""
    stripped = version.strip()
    return bool(stripped) and not any(c in stripped for c in (">", "<", "~", "^", "*", "!"))


def compute_pinning_status(
    project: str,
    statuses: List[DependencyStatus],
) -> List[PinningEntry]:
    """Build a PinningEntry for every dependency in *statuses*."""
    entries: List[PinningEntry] = []
    for s in statuses:
        pinned = _looks_pinned(s.current_version)
        outdated = s.is_outdated
        matches = pinned and not outdated
        entries.append(
            PinningEntry(
                project=project,
                package=s.package,
                current_version=s.current_version,
                latest_version=s.latest_version,
                is_pinned=pinned,
                is_outdated=outdated,
                pin_matches_latest=matches,
            )
        )
    return entries


def format_pinning_report(entries: List[PinningEntry]) -> str:
    """Return a human-readable pinning status report."""
    if not entries:
        return "No dependencies to report."

    lines = [f"Pinning status — {entries[0].project}", ""]
    for e in entries:
        pin_tag = "[pinned]" if e.is_pinned else "[unpinned]"
        status_tag = "outdated" if e.is_outdated else "up-to-date"
        match_tag = " ✓ matches latest" if e.pin_matches_latest else ""
        lines.append(
            f"  {e.package:<30} {e.current_version:<15} {pin_tag:<12} {status_tag}{match_tag}"
        )

    pinned = sum(1 for e in entries if e.is_pinned)
    unpinned = len(entries) - pinned
    outdated_pinned = sum(1 for e in entries if e.is_pinned and e.is_outdated)
    lines += [
        "",
        f"Total: {len(entries)}  Pinned: {pinned}  Unpinned: {unpinned}  "
        f"Pinned-but-outdated: {outdated_pinned}",
    ]
    return "\n".join(lines)
