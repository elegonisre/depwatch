"""CLI commands for the dependency graph feature."""
from __future__ import annotations

import json
from typing import Dict, List

import click

from depwatch.checker import check_dependencies
from depwatch.config import load_config
from depwatch.dependency_graph import build_graph, format_graph_report, shared_outdated


@click.group("graph")
def graph_cmd() -> None:
    """Analyse dependency relationships across projects."""


@graph_cmd.command("show")
@click.option("--config", "config_path", default="depwatch.toml", show_default=True)
@click.option("--format", "fmt", type=click.Choice(["text", "json"]), default="text")
def show_cmd(config_path: str, fmt: str) -> None:
    """Show the full dependency graph report."""
    try:
        cfg = load_config(config_path)
    except FileNotFoundError:
        click.echo(f"Config file not found: {config_path}", err=True)
        raise SystemExit(1)

    project_statuses = {
        p.name: check_dependencies(p.requirements) for p in cfg.projects
    }
    graph = build_graph(project_statuses)

    if fmt == "json":
        data = [
            {
                "project": n.project,
                "package": n.package,
                "current_version": n.current_version,
                "latest_version": n.latest_version,
                "is_outdated": n.is_outdated,
                "dependents": n.dependents,
            }
            for n in graph.nodes
        ]
        click.echo(json.dumps(data, indent=2))
    else:
        click.echo(format_graph_report(graph))


@graph_cmd.command("shared-outdated")
@click.option("--config", "config_path", default="depwatch.toml", show_default=True)
def shared_outdated_cmd(config_path: str) -> None:
    """List packages that are outdated in more than one project."""
    try:
        cfg = load_config(config_path)
    except FileNotFoundError:
        click.echo(f"Config file not found: {config_path}", err=True)
        raise SystemExit(1)

    project_statuses = {
        p.name: check_dependencies(p.requirements) for p in cfg.projects
    }
    graph = build_graph(project_statuses)
    shared = shared_outdated(graph)

    if not shared:
        click.echo("No shared outdated packages found.")
        return

    click.echo("Shared outdated packages:")
    for pkg, projects in sorted(shared.items()):
        click.echo(f"  {pkg}: {', '.join(projects)}")
