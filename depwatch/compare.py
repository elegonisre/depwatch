"""Compare dependency status across two projects."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, List, Optional
from depwatch.checker import DependencyStatus


@dataclass
class CompareEntry:
    package: str
    project_a: Optional[str]  # installed version or None if absent
    project_b: Optional[str]
    latest: Optional[str]
    only_in_a: bool
    only_in_b: bool
    version_differs: bool


def _index(statuses: List[DependencyStatus]) -> Dict[str, DependencyStatus]:
    return {s.package: s for s in statuses}


def compare_projects(
    name_a: str,
    statuses_a: List[DependencyStatus],
    name_b: str,
    statuses_b: List[DependencyStatus],
) -> List[CompareEntry]:
    """Return per-package comparison between two projects."""
    idx_a = _index(statuses_a)
    idx_b = _index(statuses_b)
    all_packages = sorted(set(idx_a) | set(idx_b))
    entries: List[CompareEntry] = []
    for pkg in all_packages:
        a = idx_a.get(pkg)
        b = idx_b.get(pkg)
        entries.append(
            CompareEntry(
                package=pkg,
                project_a=a.installed_version if a else None,
                project_b=b.installed_version if b else None,
                latest=(a or b).latest_version if (a or b) else None,
                only_in_a=b is None,
                only_in_b=a is None,
                version_differs=(
                    a is not None
                    and b is not None
                    and a.installed_version != b.installed_version
                ),
            )
        )
    return entries


def format_compare_report(
    name_a: str, name_b: str, entries: List[CompareEntry]
) -> str:
    lines = [f"Comparison: {name_a}  vs  {name_b}", "=" * 50]
    for e in entries:
        if e.only_in_a:
            lines.append(f"  {e.package}: only in {name_a} ({e.project_a})")
        elif e.only_in_b:
            lines.append(f"  {e.package}: only in {name_b} ({e.project_b})")
        elif e.version_differs:
            lines.append(
                f"  {e.package}: {name_a}={e.project_a}  {name_b}={e.project_b}  latest={e.latest}"
            )
        else:
            lines.append(f"  {e.package}: same ({e.project_a})")
    return "\n".join(lines)
