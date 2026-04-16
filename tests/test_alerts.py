"""Tests for depwatch.alerts."""

from unittest.mock import MagicMock, patch

import pytest

from depwatch.alerts import AlertConfig, format_alert_body, send_email_alert
from depwatch.checker import DependencyStatus


def _make_status(package: str, current: str, latest: str) -> DependencyStatus:
    return DependencyStatus(
        package=package,
        current_version=current,
        latest_version=latest,
        is_outdated=current != latest,
    )


def test_format_alert_body_with_outdated():
    statuses = [
        _make_status("requests", "2.28.0", "2.31.0"),
        _make_status("flask", "3.0.0", "3.0.0"),
    ]
    body = format_alert_body("my-app", statuses)
    assert "requests" in body
    assert "2.28.0" in body
    assert "2.31.0" in body
    assert "flask" not in body
    assert "my-app" in body


def test_format_alert_body_all_up_to_date():
    statuses = [_make_status("flask", "3.0.0", "3.0.0")]
    body = format_alert_body("my-app", statuses)
    assert body == ""


def test_send_email_alert_no_outdated():
    config = AlertConfig(
        smtp_host="smtp.example.com",
        smtp_port=587,
        sender="a@example.com",
        recipients=["b@example.com"],
    )
    statuses = [_make_status("flask", "3.0.0", "3.0.0")]
    result = send_email_alert(config, "my-app", statuses)
    assert result is False


@patch("depwatch.alerts.smtplib.SMTP")
def test_send_email_alert_sends_mail(mock_smtp):
    mock_server = MagicMock()
    mock_smtp.return_value.__enter__.return_value = mock_server

    config = AlertConfig(
        smtp_host="smtp.example.com",
        smtp_port=587,
        sender="a@example.com",
        recipients=["b@example.com"],
        username="user",
        password="pass",
    )
    statuses = [_make_status("requests", "2.28.0", "2.31.0")]
    result = send_email_alert(config, "my-app", statuses)

    assert result is True
    mock_server.starttls.assert_called_once()
    mock_server.login.assert_called_once_with("user", "pass")
    mock_server.sendmail.assert_called_once()
