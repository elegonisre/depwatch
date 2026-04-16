"""Notification channel abstraction for depwatch alerts."""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import List, Protocol

from depwatch.checker import DependencyStatus
from depwatch.alerts import AlertConfig, format_alert_body, send_email_alert

logger = logging.getLogger(__name__)


class NotificationChannel(Protocol):
    def send(self, project: str, statuses: List[DependencyStatus]) -> bool:
        ...


@dataclass
class EmailChannel:
    config: AlertConfig

    def send(self, project: str, statuses: List[DependencyStatus]) -> bool:
        outdated = [s for s in statuses if s.is_outdated]
        if not outdated:
            logger.debug("[email] No outdated deps for %s, skipping.", project)
            return False
        send_email_alert(project, statuses, self.config)
        logger.info("[email] Alert sent for %s (%d outdated).", project, len(outdated))
        return True


@dataclass
class LogChannel:
    level: str = "warning"

    def send(self, project: str, statuses: List[DependencyStatus]) -> bool:
        outdated = [s for s in statuses if s.is_outdated]
        if not outdated:
            return False
        log = getattr(logger, self.level.lower(), logger.warning)
        for s in outdated:
            log("[%s] %s is outdated: %s -> %s", project, s.package, s.current, s.latest)
        return True


@dataclass
class NotifierConfig:
    channels: List[NotificationChannel] = field(default_factory=list)


def notify_all(project: str, statuses: List[DependencyStatus], cfg: NotifierConfig) -> int:
    """Run all channels; return count of channels that fired."""
    fired = 0
    for ch in cfg.channels:
        try:
            if ch.send(project, statuses):
                fired += 1
        except Exception as exc:  # noqa: BLE001
            logger.error("Notification channel %s failed: %s", ch, exc)
    return fired
