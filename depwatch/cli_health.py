"""CLI commands for the project health feature."""
from __future__ import annotations

import click

from depwatch.config import load_config
from depwatch.checker import check_dependencies
from depwatch.health import compute_health, format_health_report


@click.group("health")
def health_cmd() -> None:
    """Project dependency health reports."""


@health_cmd.command("show")
@click.option("--config", "cfg_path", default="depwatch.toml", show_default=True)
@click.option("--project", default=None, help="Limit to a single project.")
@click.option("--format", "fmt", type=click.Choice(["text", "json"]), default="text")
@click.option("--stale-days", default=30, show_default=True,
              help="Days without resolution before a dep is considered stale.")
def show_cmd(cfg_path: str, project: str | None, fmt: str, stale_days: int) -> None:
    """Show health scores for all (or one) configured project(s)."""
    try:
        cfg = load_config(cfg_path)
    except FileNotFoundError:
        raise click.ClickException(f"Config file not found: {cfg_path}")

    projects = cfg.projects
    if project:
        projects = [p for p in projects if p.name == project]
        if not projects:
            raise click.ClickException(f"Project '{project}' not found in config.")

    reports = []
    for proj in projects:
        statuses = check_dependencies(proj.name, proj.requirements)
        reports.append(compute_health(proj.name, statuses, stale_days=stale_days))

    click.echo(format_health_report(reports, fmt=fmt))


@health_cmd.command("check")
@click.option("--config", "cfg_path", default="depwatch.toml", show_default=True)
@click.option("--min-score", default=70.0, show_default=True,
              help="Exit non-zero if any project scores below this threshold.")
@click.option("--stale-days", default=30, show_default=True)
def check_cmd(cfg_path: str, min_score: float, stale_days: int) -> None:
    """Fail (exit 1) if any project health score is below --min-score."""
    try:
        cfg = load_config(cfg_path)
    except FileNotFoundError:
        raise click.ClickException(f"Config file not found: {cfg_path}")

    failed = []
    for proj in cfg.projects:
        statuses = check_dependencies(proj.name, proj.requirements)
        report = compute_health(proj.name, statuses, stale_days=stale_days)
        click.echo(f"{proj.name}: {report.summary}")
        if report.score < min_score:
            failed.append(proj.name)

    if failed:
        raise click.ClickException(
            f"Health check failed for: {', '.join(failed)} "
            f"(min score: {min_score})"
        )
    click.echo("All projects meet the minimum health score.")
