"""CLI commands for dependency maturity reporting."""

from __future__ import annotations

import json
import sys

import click

from depwatch.checker import check_dependencies
from depwatch.config import load_config
from depwatch.maturity import compute_maturity, format_maturity_report


@click.group("maturity")
def maturity_cmd() -> None:
    """Dependency maturity commands."""


@maturity_cmd.command("show")
@click.option("--config", default="depwatch.toml", show_default=True, help="Config file.")
@click.option("--project", default=None, help="Limit to a single project name.")
@click.option(
    "--format",
    "fmt",
    default="text",
    type=click.Choice(["text", "json"]),
    show_default=True,
)
@click.option("--min-score", default=None, type=float, help="Only show entries below this score.")
def show_cmd(config: str, project: str | None, fmt: str, min_score: float | None) -> None:
    """Show maturity scores for all tracked dependencies."""
    try:
        cfg = load_config(config)
    except FileNotFoundError:
        click.echo(f"Config file not found: {config}", err=True)
        sys.exit(1)

    all_entries = []
    for proj in cfg.projects:
        if project and proj.name != project:
            continue
        statuses = check_dependencies(proj.requirements)
        entries = compute_maturity(statuses, project=proj.name)
        if min_score is not None:
            entries = [e for e in entries if e.maturity_score < min_score]
        all_entries.extend(entries)

    if fmt == "json":
        data = [
            {
                "project": e.project,
                "package": e.package,
                "current_version": e.current_version,
                "latest_version": e.latest_version,
                "major_version": e.major_version,
                "is_outdated": e.is_outdated,
                "versions_behind": e.versions_behind,
                "maturity_score": e.maturity_score,
                "label": e.label,
            }
            for e in all_entries
        ]
        click.echo(json.dumps(data, indent=2))
    else:
        click.echo(format_maturity_report(all_entries))
