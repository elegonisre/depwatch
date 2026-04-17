"""Main CLI entry point for depwatch."""
from __future__ import annotations

from pathlib import Path

import click

from depwatch.checker import check_dependencies
from depwatch.config import load_config
from depwatch.reporter import generate_report
from depwatch.scheduler import run_scheduler
from depwatch.history import load_history, clear_history
from depwatch.trend import outdated_counts_over_time, most_frequently_outdated
from depwatch.cli_digest import digest_cmd
from depwatch.cli_baseline import baseline_cmd


@click.group()
def cli() -> None:
    """depwatch — monitor outdated Python dependencies."""


@cli.command("check")
@click.option("--config", "config_path", default="depwatch.toml", show_default=True)
@click.option("--format", "fmt", type=click.Choice(["text", "json"]), default="text", show_default=True)
def check_cmd(config_path: str, fmt: str) -> None:
    """Check dependency status for all configured projects."""
    cfg = load_config(Path(config_path))
    for project in cfg.projects:
        statuses = check_dependencies(project.packages)
        click.echo(generate_report(project.name, statuses, fmt))


@cli.command("watch")
@click.option("--config", "config_path", default="depwatch.toml", show_default=True)
@click.option("--interval", default="1h", show_default=True, help="e.g. 30m, 1h, 3600s")
def watch_cmd(config_path: str, interval: str) -> None:
    """Continuously check dependencies on a schedule."""
    cfg = load_config(Path(config_path))
    run_scheduler(cfg, interval)


@cli.command("history")
@click.argument("project")
@click.option("--limit", default=10, show_default=True)
def history_cmd(project: str, limit: int) -> None:
    """Show recent history for PROJECT."""
    records = load_history()
    project_records = [r for r in records if r.get("project") == project][-limit:]
    if not project_records:
        click.echo(f"No history found for '{project}'.")
        return
    for rec in project_records:
        click.echo(f"[{rec['timestamp']}] outdated={rec['outdated_count']} total={rec['total']}")


@cli.command("trend")
@click.argument("project")
@click.option("--top", default=5, show_default=True)
def trend_cmd(project: str, top: int) -> None:
    """Show outdated trends for PROJECT."""
    records = load_history()
    counts = outdated_counts_over_time(records, project)
    frequent = most_frequently_outdated(records, project, top)
    click.echo(f"Outdated counts over time for '{project}':")
    for ts, count in counts:
        click.echo(f"  {ts}: {count}")
    click.echo(f"\nMost frequently outdated (top {top}):")
    for pkg, n in frequent:
        click.echo(f"  {pkg}: {n} times")


@cli.command("clear-history")
def clear_history_cmd() -> None:
    """Clear all stored history."""
    clear_history()
    click.echo("History cleared.")


cli.add_command(digest_cmd, "digest")
cli.add_command(baseline_cmd, "baseline")


if __name__ == "__main__":
    cli()
