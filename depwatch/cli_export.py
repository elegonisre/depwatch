"""CLI command for exporting dependency results."""
from __future__ import annotations

import sys

import click

from depwatch.checker import check_dependencies
from depwatch.config import load_config
from depwatch.export import export_results


@click.group("export")
def export_cmd() -> None:
    """Export dependency results to a file or stdout."""


@export_cmd.command("run")
@click.option("--config", default="depwatch.toml", show_default=True, help="Config file.")
@click.option(
    "--format", "fmt", type=click.Choice(["csv", "json"]), default="json", show_default=True
)
@click.option("--output", "-o", default="-", help="Output file path, or '-' for stdout.")
@click.option("--project", default=None, help="Limit to a single project name.")
def run_cmd(config: str, fmt: str, output: str, project: str | None) -> None:
    """Check dependencies and export results."""
    cfg = load_config(config)
    projects = [
        p for p in cfg.projects if project is None or p.name == project
    ]
    if not projects:
        click.echo("No matching projects found.", err=True)
        sys.exit(1)

    all_lines: list[str] = []
    for proj in projects:
        statuses = check_dependencies(proj.dependencies)
        all_lines.append(export_results(proj.name, statuses, fmt))

    combined = "\n".join(all_lines)
    if output == "-":
        click.echo(combined)
    else:
        with open(output, "w", encoding="utf-8") as fh:
            fh.write(combined)
        click.echo(f"Exported to {output}")
