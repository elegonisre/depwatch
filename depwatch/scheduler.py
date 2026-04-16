"""Scheduled dependency checks for depwatch."""

import logging
import time
from datetime import datetime
from typing import Callable, Optional

logger = logging.getLogger(__name__)


def parse_interval(interval_str: str) -> int:
    """Parse interval string like '1h', '30m', '86400s' into seconds."""
    unit = interval_str[-1].lower()
    value = int(interval_str[:-1])
    if unit == 'h':
        return value * 3600
    elif unit == 'm':
        return value * 60
    elif unit == 's':
        return value
    raise ValueError(f"Unknown interval unit '{unit}'. Use h, m, or s.")


def run_scheduler(
    check_fn: Callable[[], None],
    interval_str: str,
    max_runs: Optional[int] = None,
) -> None:
    """Run check_fn repeatedly at the given interval.

    Args:
        check_fn: Function to call on each tick.
        interval_str: Interval string, e.g. '6h', '30m'.
        max_runs: Stop after this many runs (None = run forever).
    """
    interval_seconds = parse_interval(interval_str)
    runs = 0

    logger.info(
        "Scheduler started: interval=%s (%ds)", interval_str, interval_seconds
    )

    while max_runs is None or runs < max_runs:
        start = datetime.utcnow()
        logger.info("Running scheduled check at %s", start.isoformat())
        try:
            check_fn()
        except Exception as exc:  # noqa: BLE001
            logger.error("Scheduled check failed: %s", exc)
        runs += 1
        if max_runs is not None and runs >= max_runs:
            break
        logger.debug("Sleeping %ds until next run.", interval_seconds)
        time.sleep(interval_seconds)

    logger.info("Scheduler finished after %d run(s).", runs)
