"""Upgrade recommendation engine for depwatch."""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from depwatch.checker import DependencyStatus
from depwatch.risk import RiskEntry, assess_risk


@dataclass
class Recommendation:
    project: str
    package: str
    current_version: str
    latest_version: str
    risk_label: str
    priority: int  # 1 = highest
    reason: str


_RISK_PRIORITY = {"critical": 1, "high": 2, "medium": 3, "low": 4}


def _priority(risk_label: str) -> int:
    return _RISK_PRIORITY.get(risk_label.lower(), 5)


def build_recommendations(
    statuses: List[DependencyStatus],
    top_n: Optional[int] = None,
) -> List[Recommendation]:
    """Return upgrade recommendations sorted by priority (highest risk first)."""
    risk_entries: List[RiskEntry] = assess_risk(statuses)
    risk_map = {(r.project, r.package): r for r in risk_entries}

    recs: List[Recommendation] = []
    for s in statuses:
        if s.is_up_to_date:
            continue
        key = (s.project, s.package)
        risk = risk_map.get(key)
        label = risk.risk_label if risk else "low"
        reason = _build_reason(s, risk)
        recs.append(
            Recommendation(
                project=s.project,
                package=s.package,
                current_version=s.current_version,
                latest_version=s.latest_version,
                risk_label=label,
                priority=_priority(label),
                reason=reason,
            )
        )

    recs.sort(key=lambda r: (r.priority, r.project, r.package))
    if top_n is not None:
        recs = recs[:top_n]
    return recs


def _build_reason(s: DependencyStatus, risk: Optional[RiskEntry]) -> str:
    parts = [f"Upgrade {s.package} from {s.current_version} to {s.latest_version}"]
    if risk and risk.major_gap > 0:
        parts.append(f"{risk.major_gap} major version(s) behind")
    elif risk and risk.minor_gap > 0:
        parts.append(f"{risk.minor_gap} minor version(s) behind")
    return "; ".join(parts)


def format_recommendations(recs: List[Recommendation]) -> str:
    if not recs:
        return "No upgrade recommendations — all dependencies are up to date."
    lines = ["Upgrade Recommendations", "=" * 40]
    for i, r in enumerate(recs, 1):
        lines.append(
            f"{i}. [{r.risk_label.upper()}] {r.project}/{r.package}: {r.reason}"
        )
    return "\n".join(lines)
