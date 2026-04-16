"""Alert system for depwatch — sends notifications when outdated dependencies are found."""

from __future__ import annotations

import smtplib
from dataclasses import dataclass
from email.mime.text import MIMEText
from typing import List

from depwatch.checker import DependencyStatus


@dataclass
class AlertConfig:
    smtp_host: str
    smtp_port: int
    sender: str
    recipients: List[str]
    username: str = ""
    password: str = ""
    use_tls: bool = True


def format_alert_body(project: str, statuses: List[DependencyStatus]) -> str:
    """Build a plain-text alert message listing outdated dependencies."""
    outdated = [s for s in statuses if s.is_outdated]
    if not outdated:
        return ""

    lines = [f"Outdated dependencies detected in project: {project}", ""]
    for dep in outdated:
        lines.append(
            f"  {dep.package}: {dep.current_version} -> {dep.latest_version}"
        )
    lines.append("")
    lines.append("Please update your dependencies.")
    return "\n".join(lines)


def send_email_alert(
    config: AlertConfig,
    project: str,
    statuses: List[DependencyStatus],
) -> bool:
    """Send an email alert. Returns True if sent, False if nothing to report."""
    body = format_alert_body(project, statuses)
    if not body:
        return False

    msg = MIMEText(body)
    msg["Subject"] = f"[depwatch] Outdated dependencies in {project}"
    msg["From"] = config.sender
    msg["To"] = ", ".join(config.recipients)

    with smtplib.SMTP(config.smtp_host, config.smtp_port) as server:
        if config.use_tls:
            server.starttls()
        if config.username and config.password:
            server.login(config.username, config.password)
        server.sendmail(config.sender, config.recipients, msg.as_string())

    return True
