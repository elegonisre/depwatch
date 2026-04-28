"""CLI surface for the reachability feature."""
from __future__ import annotations

import json

import click

from depwatch.checker import check_dependencies
from depwatch.config import load_config
from depwatch.reachability import check_all_reachability, format_reachability_report


@click.group("reachability")
def reachability_cmd() -> None:
    """Detect yanked or unreachable package versions on PyPI."""


@reachability_cmd.command("show")
@click.option("--config", default="depwatch.toml", show_default=True)
@click.option("--project", default=None, help="Limit to a single project name.")
@click.option("--yanked-only", is_flag=True, default=False, help="Only show yanked packages.")
@click.option("--format", "fmt", type=click.Choice(["text", "json"]), default="text", show_default=True)
def show_cmd(config: str, project: str | None, yanked_only: bool, fmt: str) -> None:
    """Check whether installed versions have been yanked on PyPI."""
    try:
        cfg = load_config(config)
    except FileNotFoundError:
        raise click.ClickException(f"Config file not found: {config}")

    projects = [
        p for p in cfg.projects if project is None or p.name == project
    ]
    if not projects:
        raise click.ClickException(f"No project matched: {project}")

    all_statuses = []
    for proj in projects:
        all_statuses.extend(check_dependencies(proj.name, proj.requirements))

    entries = check_all_reachability(all_statuses)

    if yanked_only:
        entries = [e for e in entries if e.yanked]

    if fmt == "json":
        data = [
            {
                "project": e.project,
                "package": e.package,
                "current_version": e.current_version,
                "yanked": e.yanked,
                "yanked_reason": e.yanked_reason,
                "error": e.error,
            }
            for e in entries
        ]
        click.echo(json.dumps(data, indent=2))
    else:
        click.echo(format_reachability_report(entries))
