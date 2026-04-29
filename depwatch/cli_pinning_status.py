"""CLI commands for the pinning-status feature."""
from __future__ import annotations

import json
import sys

import click

from depwatch.checker import check_dependencies
from depwatch.config import load_config
from depwatch.pinning_status import compute_pinning_status, format_pinning_report


@click.group("pinning")
def pinning_cmd() -> None:
    """Inspect dependency pinning status across projects."""


@pinning_cmd.command("show")
@click.option("--config", "config_path", default="depwatch.toml", show_default=True)
@click.option("--project", default=None, help="Limit to a single project name.")
@click.option("--format", "fmt", type=click.Choice(["text", "json"]), default="text")
@click.option("--unpinned-only", is_flag=True, default=False, help="Show only unpinned deps.")
def show_cmd(config_path: str, project: str | None, fmt: str, unpinned_only: bool) -> None:
    """Show pinning status for all (or one) project(s)."""
    try:
        cfg = load_config(config_path)
    except FileNotFoundError:
        click.echo(f"Config file not found: {config_path}", err=True)
        sys.exit(1)

    all_entries = []
    for proj in cfg.projects:
        if project and proj.name != project:
            continue
        statuses = check_dependencies(proj.requirements)
        entries = compute_pinning_status(proj.name, statuses)
        if unpinned_only:
            entries = [e for e in entries if not e.is_pinned]
        all_entries.extend(entries)

    if fmt == "json":
        click.echo(
            json.dumps(
                [
                    {
                        "project": e.project,
                        "package": e.package,
                        "current_version": e.current_version,
                        "latest_version": e.latest_version,
                        "is_pinned": e.is_pinned,
                        "is_outdated": e.is_outdated,
                        "pin_matches_latest": e.pin_matches_latest,
                    }
                    for e in all_entries
                ],
                indent=2,
            )
        )
    else:
        if not all_entries:
            click.echo("No dependencies found.")
            return
        # Group by project for text output
        projects_seen: list[str] = []
        grouped: dict[str, list] = {}
        for e in all_entries:
            grouped.setdefault(e.project, []).append(e)
            if e.project not in projects_seen:
                projects_seen.append(e.project)
        for pname in projects_seen:
            click.echo(format_pinning_report(grouped[pname]))
            click.echo()
