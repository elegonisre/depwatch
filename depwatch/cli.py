"""Command-line interface for depwatch."""
from __future__ import annotations

import sys

import click

from depwatch.alerts import send_email_alert
from depwatch.checker import check_dependencies
from depwatch.config import load_config
from depwatch.reporter import generate_report


@click.group()
def cli() -> None:
    """depwatch — monitor outdated Python dependencies."""


@cli.command("check")
@click.option(
    "--config",
    "config_path",
    default="depwatch.toml",
    show_default=True,
    help="Path to depwatch configuration file.",
)
@click.option(
    "--format",
    "fmt",
    type=click.Choice(["text", "json"]),
    default="text",
    show_default=True,
    help="Output format for the report.",
)
@click.option(
    "--alert/--no-alert",
    default=False,
    show_default=True,
    help="Send email alert if outdated dependencies are found.",
)
def check_cmd(config_path: str, fmt: str, alert: bool) -> None:
    """Check dependencies for all configured projects."""
    try:
        config = load_config(config_path)
    except FileNotFoundError:
        click.echo(f"Config file not found: {config_path}", err=True)
        sys.exit(1)

    any_outdated = False

    for project in config.projects:
        click.echo(f"Checking {project.name} …", err=True)
        statuses = check_dependencies(project.requirements)
        report = generate_report(project.name, statuses, fmt=fmt)
        click.echo(report)

        outdated = [s for s in statuses if s.is_outdated]
        if outdated:
            any_outdated = True

        if alert and config.alert and outdated:
            send_email_alert(config.alert, project.name, statuses)
            click.echo(f"Alert sent for {project.name}.", err=True)

    sys.exit(1 if any_outdated else 0)


if __name__ == "__main__":
    cli()
