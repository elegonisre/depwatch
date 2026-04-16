"""CLI entry point for depwatch."""

from __future__ import annotations

import click

from depwatch.checker import check_dependencies
from depwatch.config import load_config
from depwatch.reporter import generate_report
from depwatch.alerts import send_email_alert
from depwatch.history import save_run, get_project_history, clear_history
from depwatch.scheduler import run_scheduler
from depwatch.trend import most_frequently_outdated, latest_snapshot


@click.group()
def cli() -> None:
    """depwatch — monitor outdated Python dependencies."""


@cli.command("check")
@click.option("--config", default="depwatch.toml", show_default=True)
@click.option("--format", "fmt", default="text", type=click.Choice(["text", "json"]))
@click.option("--save-history", is_flag=True, default=False)
def check_cmd(config: str, fmt: str, save_history: bool) -> None:
    """Run a one-off dependency check for all configured projects."""
    cfg = load_config(config)
    for project in cfg.projects:
        statuses = check_dependencies(project.dependencies)
        click.echo(generate_report(project.name, statuses, fmt))
        if cfg.alert and any(s.outdated for s in statuses):
            send_email_alert(cfg.alert, project.name, statuses)
        if save_history:
            save_run(project.name, statuses)


@cli.command("watch")
@click.option("--config", default="depwatch.toml", show_default=True)
@click.option("--interval", default="1h", show_default=True)
def watch_cmd(config: str, interval: str) -> None:
    """Repeatedly run checks on a schedule."""
    cfg = load_config(config)
    run_scheduler(interval, lambda: _run_check(cfg))


@cli.command("history")
@click.argument("project")
def history_cmd(project: str) -> None:
    """Show check history for a project."""
    records = get_project_history(project)
    if not records:
        click.echo(f"No history found for project '{project}'.")
        return
    for rec in records:
        status = "OUTDATED" if rec["outdated"] else "ok"
        click.echo(f"[{rec['checked_at']}] {rec['package']} {rec['current_version']} -> {rec['latest_version']} ({status})")


@cli.command("trend")
@click.argument("project")
def trend_cmd(project: str) -> None:
    """Show the most frequently outdated packages for a project."""
    records = get_project_history(project)
    top = most_frequently_outdated(records)
    if not top:
        click.echo("No outdated history found.")
        return
    click.echo(f"Most frequently outdated packages in '{project}':")
    for entry in top:
        click.echo(f"  {entry['package']}: outdated in {entry['outdated_count']} run(s)")


def _run_check(cfg) -> None:
    for project in cfg.projects:
        statuses = check_dependencies(project.dependencies)
        click.echo(generate_report(project.name, statuses, "text"))
        if cfg.alert and any(s.outdated for s in statuses):
            send_email_alert(cfg.alert, project.name, statuses)
