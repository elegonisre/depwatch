"""Retention policy: automatically prune history entries older than a given age."""
from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import List

from depwatch.history import load_history, _HISTORY_FILE


@dataclass
class RetentionResult:
    total_before: int
    total_after: int
    removed: int


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _parse_ts(ts: str) -> datetime:
    """Parse an ISO-8601 timestamp, attaching UTC if naive."""
    dt = datetime.fromisoformat(ts)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def apply_retention(
    max_days: int,
    history_file: Path = _HISTORY_FILE,
    *,
    _now: datetime | None = None,
) -> RetentionResult:
    """Remove history runs older than *max_days* days.

    Returns a :class:`RetentionResult` describing how many records were pruned.
    """
    if max_days <= 0:
        raise ValueError("max_days must be a positive integer")

    now = _now or _utcnow()
    cutoff = now - timedelta(days=max_days)

    records = load_history(history_file)
    total_before = len(records)

    kept: List[dict] = []
    for rec in records:
        ts_str = rec.get("timestamp", "")
        try:
            ts = _parse_ts(ts_str)
        except (ValueError, TypeError):
            kept.append(rec)  # keep malformed entries untouched
            continue
        if ts >= cutoff:
            kept.append(rec)

    total_after = len(kept)
    removed = total_before - total_after

    if removed:
        history_file.parent.mkdir(parents=True, exist_ok=True)
        with history_file.open("w", encoding="utf-8") as fh:
            json.dump(kept, fh, indent=2)

    return RetentionResult(
        total_before=total_before,
        total_after=total_after,
        removed=removed,
    )


def format_retention_report(result: RetentionResult) -> str:
    lines = [
        "Retention policy applied",
        f"  Records before : {result.total_before}",
        f"  Records removed: {result.removed}",
        f"  Records after  : {result.total_after}",
    ]
    return "\n".join(lines)
