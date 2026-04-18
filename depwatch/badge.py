"""Generate status badge data for a project's dependency health."""
from __future__ import annotations
from dataclasses import dataclass
from typing import List
from depwatch.checker import DependencyStatus


@dataclass
class BadgeData:
    label: str
    message: str
    color: str


def _outdated_count(statuses: List[DependencyStatus]) -> int:
    return sum(1 for s in statuses if s.is_outdated)


def get_badge_color(outdated: int, total: int) -> str:
    if total == 0:
        return "lightgrey"
    ratio = outdated / total
    if outdated == 0:
        return "brightgreen"
    if ratio <= 0.2:
        return "yellow"
    if ratio <= 0.5:
        return "orange"
    return "red"


def build_badge(project_name: str, statuses: List[DependencyStatus]) -> BadgeData:
    """Return badge metadata for the given project's dependency statuses."""
    total = len(statuses)
    outdated = _outdated_count(statuses)
    color = get_badge_color(outdated, total)
    message = f"{outdated}/{total} outdated" if total > 0 else "no deps"
    return BadgeData(label=project_name, message=message, color=color)


def badge_to_shields_url(badge: BadgeData) -> str:
    """Return a shields.io URL for the badge."""
    from urllib.parse import quote
    label = quote(badge.label, safe="")
    message = quote(badge.message, safe="")
    return f"https://img.shields.io/badge/{label}-{message}-{badge.color}"
