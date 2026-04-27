"""CLI commands for the dependency drift feature."""
from __future__ import annotations

import json

import click

from depwatch.checker import check_dependencies
from depwatch.config import load_config
from depwatch.drift import compute_drift, format_drift_report


@click.group("drift")
def drift_cmd() -> None:
    """Analyse how far dependencies have drifted from their latest versions."""


@drift_cmd.command("show")
@click.option("--config", "config_path", default="depwatch.toml", show_default=True)
@click.option("--project", "project_filter", default=None, help="Limit to one project.")
@click.option("--format", "fmt", type=click.Choice(["text", "json"]), default="text")
@click.option("--min-score", default=0.0, show_default=True, help="Only show entries with drift score >= this value.")
def show_cmd(config_path: str, project_filter: str | None, fmt: str, min_score: float) -> None:
    """Show drift scores for all (or a specific) project."""
    try:
        cfg = load_config(config_path)
    except FileNotFoundError:
        raise click.ClickException(f"Config file not found: {config_path}")

    all_entries = []
    for project in cfg.projects:
        if project_filter and project.name != project_filter:
            continue
        statuses = check_dependencies(project.name, project.requirements)
        entries = compute_drift(project.name, statuses)
        all_entries.extend(e for e in entries if e.drift_score >= min_score)

    if fmt == "json":
        data = [
            {
                "project": e.project,
                "package": e.package,
                "current_version": e.current_version,
                "latest_version": e.latest_version,
                "major_gap": e.major_gap,
                "minor_gap": e.minor_gap,
                "patch_gap": e.patch_gap,
                "drift_score": e.drift_score,
            }
            for e in all_entries
        ]
        click.echo(json.dumps(data, indent=2))
    else:
        click.echo(format_drift_report(all_entries))
