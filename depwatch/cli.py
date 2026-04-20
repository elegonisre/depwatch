"""Main CLI entry point for depwatch."""
from __future__ import annotations

import click

from depwatch.cli_baseline import baseline_cmd
from depwatch.cli_digest import digest_cmd
from depwatch.cli_export import export_cmd
from depwatch.cli_filter import filter_cmd
from depwatch.cli_groupby import group_cmd
from depwatch.cli_ignore import ignore_cmd
from depwatch.cli_pin import pin_cmd
from depwatch.cli_score import score_cmd
from depwatch.cli_suppress import suppress_cmd
from depwatch.cli_risk import risk_cmd
from depwatch.cli_policy import policy_cmd
from depwatch.cli_audit import audit_cmd
from depwatch.config import load_config
from depwatch.checker import check_dependencies
from depwatch.reporter import generate_report
from depwatch.scheduler import run_scheduler
from depwatch.history import save_run, load_history
from depwatch.trend import outdated_counts_over_time, most_frequently_outdated

from pathlib import Path


@click.group()
def cli():
    """depwatch — monitor outdated Python dependencies."""


@cli.command("check")
@click.option("--config", "cfg_path", default="depwatch.toml", show_default=True)
@click.option("--format", "fmt", default="text", type=click.Choice(["text", "json"]), show_default=True)
def check_cmd(cfg_path: str, fmt: str):
    """Check dependencies for all configured projects."""
    cfg = load_config(Path(cfg_path))
    all_statuses = []
    for project in cfg.projects:
        statuses = check_dependencies(project.requirements)
        all_statuses.extend(statuses)
        save_run(project.name, statuses)
    click.echo(generate_report(cfg.projects[0].name if cfg.projects else "unknown", all_statuses, fmt))


@cli.command("watch")
@click.option("--config", "cfg_path", default="depwatch.toml", show_default=True)
@click.option("--interval", default="1h", show_default=True)
def watch_cmd(cfg_path: str, interval: str):
    """Continuously watch dependencies at a given interval."""
    cfg = load_config(Path(cfg_path))
    run_scheduler(cfg, interval)


@cli.command("history")
@click.option("--project", required=True)
def history_cmd(project: str):
    """Show run history for a project."""
    records = load_history()
    project_records = [r for r in records if r.get("project") == project]
    if not project_records:
        click.echo(f"No history found for project '{project}'.")
        return
    for rec in project_records:
        click.echo(f"{rec['timestamp']}: {rec['outdated']}/{rec['total']} outdated")


@cli.command("trend")
@click.option("--project", required=True)
@click.option("--top", default=5, show_default=True)
def trend_cmd(project: str, top: int):
    """Show outdated trends for a project."""
    records = load_history()
    counts = outdated_counts_over_time(records, project)
    frequent = most_frequently_outdated(records, project, top_n=top)
    click.echo(f"Outdated counts over time for '{project}':")
    for ts, count in counts:
        click.echo(f"  {ts}: {count}")
    click.echo(f"\nMost frequently outdated (top {top}):")
    for pkg, freq in frequent:
        click.echo(f"  {pkg}: {freq} times")


cli.add_command(baseline_cmd, "baseline")
cli.add_command(digest_cmd, "digest")
cli.add_command(export_cmd, "export")
cli.add_command(filter_cmd, "filter")
cli.add_command(group_cmd, "group")
cli.add_command(ignore_cmd, "ignore")
cli.add_command(pin_cmd, "pin")
cli.add_command(score_cmd, "score")
cli.add_command(suppress_cmd, "suppress")
cli.add_command(risk_cmd, "risk")
cli.add_command(policy_cmd, "policy")
cli.add_command(audit_cmd, "audit")

if __name__ == "__main__":
    cli()
