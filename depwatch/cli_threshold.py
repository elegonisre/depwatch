"""CLI commands for threshold enforcement."""
from __future__ import annotations

import sys

import click

from depwatch.checker import check_dependencies
from depwatch.config import load_config
from depwatch.threshold import ThresholdConfig, evaluate_threshold, format_threshold_result


@click.group("threshold")
def threshold_cmd() -> None:
    """Enforce outdated-dependency thresholds."""


@threshold_cmd.command("check")
@click.option("--config", "config_path", default="depwatch.toml", show_default=True)
@click.option("--max-outdated", type=int, default=None, help="Hard limit on outdated count.")
@click.option("--max-ratio", type=float, default=None, help="Hard limit on outdated ratio (0-1).")
@click.option("--warn-outdated", type=int, default=None, help="Warn when outdated count reaches this.")
@click.option("--warn-ratio", type=float, default=None, help="Warn when outdated ratio reaches this.")
@click.option("--project", "project_name", default=None, help="Limit to a single project.")
def check_cmd(
    config_path: str,
    max_outdated: int | None,
    max_ratio: float | None,
    warn_outdated: int | None,
    warn_ratio: float | None,
    project_name: str | None,
) -> None:
    """Check all projects against the given thresholds."""
    cfg = load_config(config_path)
    tc = ThresholdConfig(
        max_outdated=max_outdated,
        max_outdated_ratio=max_ratio,
        warn_outdated=warn_outdated,
        warn_ratio=warn_ratio,
    )

    projects = [
        p for p in cfg.projects
        if project_name is None or p.name == project_name
    ]

    exit_code = 0
    for project in projects:
        statuses = check_dependencies(project.requirements)
        result = evaluate_threshold(statuses, tc)
        click.echo(f"\n=== {project.name} ===")
        click.echo(format_threshold_result(result))
        if not result.passed:
            exit_code = 1

    sys.exit(exit_code)
