"""CLI commands for managing temporary package alert suppressions."""
from __future__ import annotations

from datetime import datetime, timezone, timedelta

import click

from depwatch.suppress import (
    suppress_package,
    remove_suppression,
    is_suppressed,
    list_suppressions,
)


@click.group("suppress")
def suppress_cmd():
    """Manage temporary alert suppressions."""


@suppress_cmd.command("add")
@click.argument("package")
@click.option("--days", default=7, show_default=True, help="Suppress for N days.")
@click.option("--reason", default="", help="Reason for suppression.")
def add_cmd(package: str, days: int, reason: str):
    """Suppress alerts for PACKAGE for a number of days."""
    until = datetime.now(timezone.utc) + timedelta(days=days)
    suppress_package(package, until, reason)
    click.echo(f"Suppressed '{package}' until {until.date()} ({days}d).")


@suppress_cmd.command("remove")
@click.argument("package")
def remove_cmd(package: str):
    """Remove suppression for PACKAGE."""
    removed = remove_suppression(package)
    if removed:
        click.echo(f"Suppression removed for '{package}'.")
    else:
        click.echo(f"No suppression found for '{package}'.")


@suppress_cmd.command("list")
def list_cmd():
    """List all suppressions."""
    entries = list_suppressions()
    if not entries:
        click.echo("No suppressions configured.")
        return
    for e in entries:
        status = "active" if e["active"] else "expired"
        reason = f" — {e['reason']}" if e["reason"] else ""
        click.echo(f"{e['package']}: until {e['until'].date()} [{status}]{reason}")
