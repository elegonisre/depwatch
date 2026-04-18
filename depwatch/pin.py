"""Pinning suggestions: recommend pinning or upgrading dependencies."""
from dataclasses import dataclass
from typing import List
from depwatch.checker import DependencyStatus


@dataclass
class PinSuggestion:
    project: str
    package: str
    current: str
    latest: str
    action: str  # 'upgrade' | 'pin'
    pin_spec: str


def suggest_pins(statuses: List[DependencyStatus], pin_to_latest: bool = False) -> List[PinSuggestion]:
    """Return pin/upgrade suggestions for outdated or unpinned deps."""
    suggestions = []
    for s in statuses:
        if s.is_outdated:
            action = "upgrade"
            pin_spec = f"{s.package}=={s.latest_version}"
            suggestions.append(PinSuggestion(
                project=s.project,
                package=s.package,
                current=s.current_version,
                latest=s.latest_version,
                action=action,
                pin_spec=pin_spec,
            ))
        elif pin_to_latest and s.current_version and "==" not in s.current_version:
            pin_spec = f"{s.package}=={s.current_version}"
            suggestions.append(PinSuggestion(
                project=s.project,
                package=s.package,
                current=s.current_version,
                latest=s.latest_version,
                action="pin",
                pin_spec=pin_spec,
            ))
    return suggestions


def format_suggestions(suggestions: List[PinSuggestion]) -> str:
    if not suggestions:
        return "No pin/upgrade suggestions."
    lines = []
    for s in suggestions:
        lines.append(f"[{s.project}] {s.action.upper()}: {s.pin_spec}  (was {s.current})")    
    return "\n".join(lines)
