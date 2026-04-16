"""Tests for depwatch.notifier."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from depwatch.checker import DependencyStatus
from depwatch.alerts import AlertConfig
from depwatch.notifier import (
    EmailChannel,
    LogChannel,
    NotifierConfig,
    notify_all,
)


def _s(pkg: str, current: str, latest: str) -> DependencyStatus:
    return DependencyStatus(
        package=pkg,
        current=current,
        latest=latest,
        is_outdated=current != latest,
    )


_ALERT_CFG = AlertConfig(
    smtp_host="localhost",
    smtp_port=25,
    sender="a@b.com",
    recipients=["x@y.com"],
)


class TestEmailChannel:
    def test_no_send_when_all_up_to_date(self):
        ch = EmailChannel(config=_ALERT_CFG)
        statuses = [_s("requests", "2.28.0", "2.28.0")]
        with patch("depwatch.notifier.send_email_alert") as mock_send:
            result = ch.send("myproject", statuses)
        assert result is False
        mock_send.assert_not_called()

    def test_sends_when_outdated(self):
        ch = EmailChannel(config=_ALERT_CFG)
        statuses = [_s("flask", "2.0.0", "3.0.0")]
        with patch("depwatch.notifier.send_email_alert") as mock_send:
            result = ch.send("myproject", statuses)
        assert result is True
        mock_send.assert_called_once()


class TestLogChannel:
    def test_no_fire_when_up_to_date(self):
        ch = LogChannel()
        assert ch.send("proj", [_s("x", "1.0", "1.0")]) is False

    def test_fires_when_outdated(self, caplog):
        import logging
        ch = LogChannel(level="warning")
        with caplog.at_level(logging.WARNING, logger="depwatch.notifier"):
            result = ch.send("proj", [_s("x", "1.0", "2.0")])
        assert result is True
        assert "x" in caplog.text


class TestNotifyAll:
    def test_counts_fired_channels(self):
        ch1, ch2 = MagicMock(return_value=True), MagicMock(return_value=False)
        ch1.send.return_value = True
        ch2.send.return_value = False
        cfg = NotifierConfig(channels=[ch1, ch2])
        fired = notify_all("p", [_s("a", "1", "2")], cfg)
        assert fired == 1

    def test_exception_in_channel_does_not_raise(self):
        ch = MagicMock()
        ch.send.side_effect = RuntimeError("boom")
        cfg = NotifierConfig(channels=[ch])
        fired = notify_all("p", [_s("a", "1", "2")], cfg)
        assert fired == 0
