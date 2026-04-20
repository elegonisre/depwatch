"""Risk scoring for outdated dependencies based on version gap and age."""
from dataclasses import dataclass
from typing import List
from depwatch.checker import DependencyStatus


@dataclass
class RiskEntry:
    project: str
    package: str
    current_version: str
    latest_version: str
    major_gap: int
    minor_gap: int
    risk_score: float  # 0.0 - 1.0
    risk_label: str   # low / medium / high / critical


def _version_parts(v: str):
    parts = []
    for p in v.split("."):
        try:
            parts.append(int(p))
        except ValueError:
            parts.append(0)
    while len(parts) < 3:
        parts.append(0)
    return parts


def _compute_gaps(current: str, latest: str):
    c = _version_parts(current)
    l = _version_parts(latest)
    major_gap = max(0, l[0] - c[0])
    minor_gap = max(0, l[1] - c[1]) if major_gap == 0 else 0
    return major_gap, minor_gap


def _risk_score(major_gap: int, minor_gap: int) -> float:
    score = min(1.0, major_gap * 0.4 + minor_gap * 0.05)
    return round(score, 2)


def _risk_label(score: float) -> str:
    if score == 0.0:
        return "low"
    if score < 0.2:
        return "low"
    if score < 0.5:
        return "medium"
    if score < 0.8:
        return "high"
    return "critical"


def assess_risk(project: str, statuses: List[DependencyStatus]) -> List[RiskEntry]:
    entries = []
    for s in statuses:
        if not s.is_outdated:
            continue
        major_gap, minor_gap = _compute_gaps(s.current_version, s.latest_version)
        score = _risk_score(major_gap, minor_gap)
        entries.append(RiskEntry(
            project=project,
            package=s.package,
            current_version=s.current_version,
            latest_version=s.latest_version,
            major_gap=major_gap,
            minor_gap=minor_gap,
            risk_score=score,
            risk_label=_risk_label(score),
        ))
    entries.sort(key=lambda e: e.risk_score, reverse=True)
    return entries


def filter_by_label(entries: List[RiskEntry], label: str) -> List[RiskEntry]:
    """Return only entries whose risk_label matches the given label.

    Args:
        entries: List of RiskEntry objects to filter.
        label: One of 'low', 'medium', 'high', or 'critical'.

    Returns:
        A filtered list containing only entries with the specified label.
    """
    valid_labels = {"low", "medium", "high", "critical"}
    if label not in valid_labels:
        raise ValueError(f"Invalid label {label!r}. Must be one of {sorted(valid_labels)}.")
    return [e for e in entries if e.risk_label == label]


def format_risk_report(entries: List[RiskEntry]) -> str:
    if not entries:
        return "No risk entries found."
    lines = [f"{'Package':<20} {'Project':<15} {'Current':<12} {'Latest':<12} {'Score':>6}  Label"]
    lines.append("-" * 75)
    for e in entries:
        lines.append(f"{e.package:<20} {e.project:<15} {e.current_version:<12} {e.latest_version:<12} {e.risk_score:>6.2f}  {e.risk_label}")
    return "\n".join(lines)
