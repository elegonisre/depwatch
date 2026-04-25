"""CLI commands for the dependency-age feature."""
from __future__ import annotations

import json

import click

from depwatch.config import load_config
from depwatch.checker import check_dependencies
from depwatch.dependency_age import compute_dependency_ages, format_age_table


@click.group("dep-age")
def dep_age_cmd() -> None:
    """Show how old each installed dependency version is."""


@dep_age_cmd.command("show")
@click.option("--config", "config_path", default="depwatch.toml", show_default=True)
@click.option("--project", default=None, help="Limit to a single project name.")
@click.option("--outdated-only", is_flag=True, default=False, help="Show only outdated deps.")
@click.option("--format", "fmt", type=click.Choice(["text", "json"]), default="text")
def show_cmd(config_path: str, project: str | None, outdated_only: bool, fmt: str) -> None:
    """Display dependency age information for configured projects."""
    try:
        cfg = load_config(config_path)
    except FileNotFoundError:
        raise click.ClickException(f"Config file not found: {config_path}")

    all_entries = []
    projects = [
        p for p in cfg.projects if project is None or p.name == project
    ]
    if not projects:
        raise click.ClickException(f"No project found: {project}")

    for proj in projects:
        statuses = check_dependencies(proj.requirements)
        entries = compute_dependency_ages(proj.name, statuses)
        if outdated_only:
            entries = [e for e in entries if e.is_outdated]
        all_entries.extend(entries)

    if fmt == "json":
        data = [
            {
                "project": e.project,
                "package": e.package,
                "installed_version": e.installed_version,
                "latest_version": e.latest_version,
                "installed_release_date": e.installed_release_date.isoformat()
                if e.installed_release_date
                else None,
                "latest_release_date": e.latest_release_date.isoformat()
                if e.latest_release_date
                else None,
                "days_behind": e.days_behind,
                "is_outdated": e.is_outdated,
            }
            for e in all_entries
        ]
        click.echo(json.dumps(data, indent=2))
    else:
        click.echo(format_age_table(all_entries))
