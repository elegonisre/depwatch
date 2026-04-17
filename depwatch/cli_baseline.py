"""CLI commands for baseline management."""
from __future__ import annotations

from pathlib import Path

import click

from depwatch.baseline import save_baseline, load_baseline, diff_from_baseline, DEFAULT_BASELINE_FILE
from depwatch.checker import check_dependencies
from depwatch.config import load_config
from depwatch.reporter import generate_report


@click.group("baseline")
def baseline_cmd() -> None:
    """Manage dependency baselines."""


@baseline_cmd.command("save")
@click.option("--config", "config_path", default="depwatch.toml", show_default=True)
@click.option("--baseline-file", default=str(DEFAULT_BASELINE_FILE), show_default=True)
def save_cmd(config_path: str, baseline_file: str) -> None:
    """Pin current dependency state as baseline."""
    cfg = load_config(Path(config_path))
    bf = Path(baseline_file)
    for project in cfg.projects:
        statuses = check_dependencies(project.packages)
        save_baseline(project.name, statuses, bf)
        click.echo(f"Baseline saved for '{project.name}' ({len(statuses)} packages).")


@baseline_cmd.command("show")
@click.argument("project")
@click.option("--baseline-file", default=str(DEFAULT_BASELINE_FILE), show_default=True)
def show_cmd(project: str, baseline_file: str) -> None:
    """Show saved baseline for PROJECT."""
    pkgs = load_baseline(project, Path(baseline_file))
    if pkgs is None:
        click.echo(f"No baseline found for '{project}'.")
        return
    for p in pkgs:
        status = "OUTDATED" if p["outdated"] else "ok"
        click.echo(f"  {p['package']:30s} {p['current']:15s} -> {p['latest']:15s} [{status}]")


@baseline_cmd.command("diff")
@click.option("--config", "config_path", default="depwatch.toml", show_default=True)
@click.option("--baseline-file", default=str(DEFAULT_BASELINE_FILE), show_default=True)
def diff_cmd(config_path: str, baseline_file: str) -> None:
    """Show what changed since the saved baseline."""
    cfg = load_config(Path(config_path))
    bf = Path(baseline_file)
    for project in cfg.projects:
        statuses = check_dependencies(project.packages)
        result = diff_from_baseline(project.name, statuses, bf)
        click.echo(f"\n=== {project.name} ===")
        for pkg in result["new_outdated"]:
            click.echo(f"  [NEW OUTDATED]     {pkg}")
        for pkg in result["resolved"]:
            click.echo(f"  [RESOLVED]         {pkg}")
        for pkg in result["version_changed"]:
            click.echo(f"  [VERSION CHANGED]  {pkg}")
        if not any(result.values()):
            click.echo("  No changes from baseline.")
