"""CLI commands for the deprecation-detection feature."""
from __future__ import annotations

import json
from typing import Optional

import click

from depwatch.checker import check_dependencies
from depwatch.config import load_config
from depwatch.deprecation import check_deprecations, format_deprecation_report


@click.group("deprecation")
def deprecation_cmd() -> None:
    """Detect deprecated packages across projects."""


@deprecation_cmd.command("show")
@click.option("--config", "config_path", default="depwatch.toml", show_default=True)
@click.option("--project", default=None, help="Limit to a single project name.")
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["text", "json"]),
    default="text",
    show_default=True,
)
@click.option("--deprecated-only", is_flag=True, default=False)
def show_cmd(
    config_path: str,
    project: Optional[str],
    output_format: str,
    deprecated_only: bool,
) -> None:
    """Show deprecation status for all (or one) project(s)."""
    try:
        cfg = load_config(config_path)
    except FileNotFoundError:
        raise click.ClickException(f"Config file not found: {config_path}")

    projects = cfg.projects
    if project:
        projects = [p for p in projects if p.name == project]
        if not projects:
            raise click.ClickException(f"Project '{project}' not found in config.")

    all_entries = []
    for proj in projects:
        statuses = check_dependencies(proj.requirements)
        entries = check_deprecations(statuses, proj.name)
        if deprecated_only:
            entries = [e for e in entries if e.deprecated]
        all_entries.extend(entries)

    if output_format == "json":
        data = [
            {
                "project": e.project,
                "package": e.package,
                "current_version": e.current_version,
                "deprecated": e.deprecated,
                "reason": e.reason,
                "successor": e.successor,
            }
            for e in all_entries
        ]
        click.echo(json.dumps(data, indent=2))
    else:
        click.echo(format_deprecation_report(all_entries))
