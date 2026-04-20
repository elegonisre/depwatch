"""Audit log: record every check run with metadata for compliance/traceability."""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

DEFAULT_AUDIT_FILE = Path("depwatch_audit.jsonl")


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class AuditEntry:
    timestamp: str
    project: str
    total: int
    outdated: int
    triggered_by: str  # e.g. "cli", "scheduler", "api"
    tags: List[str] = field(default_factory=list)
    note: Optional[str] = None


def _entry_to_dict(e: AuditEntry) -> dict:
    return {
        "timestamp": e.timestamp,
        "project": e.project,
        "total": e.total,
        "outdated": e.outdated,
        "triggered_by": e.triggered_by,
        "tags": e.tags,
        "note": e.note,
    }


def record_audit(
    project: str,
    total: int,
    outdated: int,
    triggered_by: str = "cli",
    tags: Optional[List[str]] = None,
    note: Optional[str] = None,
    audit_file: Path = DEFAULT_AUDIT_FILE,
) -> AuditEntry:
    entry = AuditEntry(
        timestamp=_utcnow().isoformat(),
        project=project,
        total=total,
        outdated=outdated,
        triggered_by=triggered_by,
        tags=tags or [],
        note=note,
    )
    with open(audit_file, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(_entry_to_dict(entry)) + "\n")
    return entry


def load_audit_log(audit_file: Path = DEFAULT_AUDIT_FILE) -> List[AuditEntry]:
    if not audit_file.exists():
        return []
    entries: List[AuditEntry] = []
    with open(audit_file, "r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            d = json.loads(line)
            entries.append(
                AuditEntry(
                    timestamp=d["timestamp"],
                    project=d["project"],
                    total=d["total"],
                    outdated=d["outdated"],
                    triggered_by=d["triggered_by"],
                    tags=d.get("tags", []),
                    note=d.get("note"),
                )
            )
    return entries


def format_audit_log(entries: List[AuditEntry]) -> str:
    if not entries:
        return "No audit records found."
    lines = [f"{'Timestamp':<30} {'Project':<20} {'Total':>6} {'Outdated':>9} {'By':<12} Tags"]
    lines.append("-" * 90)
    for e in entries:
        tags = ", ".join(e.tags) if e.tags else "-"
        lines.append(f"{e.timestamp:<30} {e.project:<20} {e.total:>6} {e.outdated:>9} {e.triggered_by:<12} {tags}")
    return "\n".join(lines)
