"""CLI commands for the variance analysis feature."""
from __future__ import annotations

import json

import click

from depwatch.config import load_config
from depwatch.variance import compute_all_variance, compute_variance, format_variance_report


@click.group("variance")
def variance_cmd() -> None:
    """Analyse how consistently projects keep dependencies up to date."""


@variance_cmd.command("show")
@click.option("--config", "config_path", default="depwatch.toml", show_default=True)
@click.option("--project", default=None, help="Limit output to a single project.")
@click.option("--format", "fmt", type=click.Choice(["text", "json"]), default="text", show_default=True)
def show_cmd(config_path: str, project: str | None, fmt: str) -> None:
    """Show variance statistics for all (or one) project(s)."""
    cfg = load_config(config_path)
    history_file: str = getattr(cfg, "history_file", ".depwatch_history.json")

    if project:
        entry = compute_variance(history_file, project)
        entries = [entry] if entry else []
    else:
        entries = compute_all_variance(history_file)

    if fmt == "json":
        click.echo(
            json.dumps(
                [
                    {
                        "project": e.project,
                        "run_count": e.run_count,
                        "mean_outdated": e.mean_outdated,
                        "variance": e.variance,
                        "std_dev": e.std_dev,
                        "min_outdated": e.min_outdated,
                        "max_outdated": e.max_outdated,
                        "stability_label": e.stability_label,
                    }
                    for e in entries
                ],
                indent=2,
            )
        )
    else:
        click.echo(format_variance_report(entries))
