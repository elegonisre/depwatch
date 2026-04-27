"""CLI commands for dependency velocity reporting."""

from __future__ import annotations

import json

import click

from depwatch.config import load_config
from depwatch.velocity import VelocityEntry, compute_velocity, format_velocity_report


@click.group("velocity")
def velocity_cmd() -> None:
    """Show how fast dependencies are going outdated."""


@velocity_cmd.command("show")
@click.option("--config", default="depwatch.toml", show_default=True)
@click.option("--history", default="depwatch_history.json", show_default=True)
@click.option("--window", default=30, show_default=True, help="Look-back window in days.")
@click.option("--format", "fmt", default="text", type=click.Choice(["text", "json"]), show_default=True)
def show_cmd(config: str, history: str, window: int, fmt: str) -> None:
    """Display velocity for every project in the config."""
    try:
        cfg = load_config(config)
    except FileNotFoundError:
        raise click.ClickException(f"Config file not found: {config}")

    entries: list[VelocityEntry] = []
    for project in cfg.projects:
        entry = compute_velocity(history, project.name, window_days=window)
        if entry is not None:
            entries.append(entry)

    if fmt == "json":
        data = [
            {
                "project": e.project,
                "outdated_per_day": round(e.outdated_per_day, 4),
                "total_outdated_delta": e.total_outdated_delta,
                "window_days": round(e.window_days, 2),
                "first_run": e.first_run.isoformat(),
                "last_run": e.last_run.isoformat(),
            }
            for e in entries
        ]
        click.echo(json.dumps(data, indent=2))
    else:
        click.echo(format_velocity_report(entries))
