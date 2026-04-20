"""CLI commands for upgrade recommendations."""
from __future__ import annotations

import json
import sys

import click

from depwatch.checker import check_dependencies
from depwatch.config import load_config
from depwatch.recommend import build_recommendations, format_recommendations


@click.group("recommend")
def recommend_cmd():
    """Upgrade recommendation commands."""


@recommend_cmd.command("show")
@click.option("--config", "cfg_path", default="depwatch.toml", show_default=True)
@click.option("--project", "project_filter", default=None, help="Limit to one project.")
@click.option("--top", "top_n", default=None, type=int, help="Show top N recommendations.")
@click.option("--format", "fmt", type=click.Choice(["text", "json"]), default="text")
def show_cmd(cfg_path: str, project_filter: str | None, top_n: int | None, fmt: str):
    """Show prioritised upgrade recommendations."""
    try:
        cfg = load_config(cfg_path)
    except FileNotFoundError:
        click.echo(f"Config file not found: {cfg_path}", err=True)
        sys.exit(1)

    projects = [
        p for p in cfg.projects
        if project_filter is None or p.name == project_filter
    ]
    if not projects:
        click.echo("No matching projects found.", err=True)
        sys.exit(1)

    all_statuses = []
    for proj in projects:
        all_statuses.extend(check_dependencies(proj))

    recs = build_recommendations(all_statuses, top_n=top_n)

    if fmt == "json":
        data = [
            {
                "project": r.project,
                "package": r.package,
                "current_version": r.current_version,
                "latest_version": r.latest_version,
                "risk_label": r.risk_label,
                "priority": r.priority,
                "reason": r.reason,
            }
            for r in recs
        ]
        click.echo(json.dumps(data, indent=2))
    else:
        click.echo(format_recommendations(recs))
