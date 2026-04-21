"""CLI commands for managing the depwatch watchlist."""
from __future__ import annotations

import click

from depwatch.checker import check_dependencies
from depwatch.config import load_config
from depwatch.watchlist import (
    add_to_watchlist,
    filter_watchlist,
    format_watchlist_report,
    load_watchlist,
    remove_from_watchlist,
)


@click.group("watchlist")
def watchlist_cmd() -> None:
    """Manage the priority watchlist for packages."""


@watchlist_cmd.command("add")
@click.argument("package")
def add_cmd(package: str) -> None:
    """Add PACKAGE to the watchlist."""
    result = add_to_watchlist(package)
    click.echo(f"Added '{package}'. Watchlist: {result}")


@watchlist_cmd.command("remove")
@click.argument("package")
def remove_cmd(package: str) -> None:
    """Remove PACKAGE from the watchlist."""
    result = remove_from_watchlist(package)
    click.echo(f"Removed '{package}'. Watchlist: {result}")


@watchlist_cmd.command("list")
def list_cmd() -> None:
    """Show all packages currently on the watchlist."""
    packages = load_watchlist()
    if not packages:
        click.echo("Watchlist is empty.")
    else:
        for pkg in packages:
            click.echo(pkg)


@watchlist_cmd.command("check")
@click.option("--config", "config_path", default="depwatch.toml", show_default=True)
def check_cmd(config_path: str) -> None:
    """Check status of all watchlisted packages across configured projects."""
    cfg = load_config(config_path)
    all_statuses = []
    for project in cfg.projects:
        all_statuses.extend(check_dependencies(project.requirements))
    watched = filter_watchlist(all_statuses)
    click.echo(format_watchlist_report(watched))
