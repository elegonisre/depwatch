"""CLI commands for the uptime feature."""
from __future__ import annotations

import json

import click

from depwatch.config import load_config
from depwatch.uptime import compute_all_uptime, compute_uptime, format_uptime_report


@click.group("uptime")
def uptime_cmd() -> None:
    """Track how long projects have stayed fully up-to-date."""


@uptime_cmd.command("show")
@click.option("--config", "cfg_path", default="depwatch.toml", show_default=True)
@click.option("--project", default=None, help="Show stats for a single project.")
@click.option("--format", "fmt", type=click.Choice(["text", "json"]), default="text")
def show_cmd(cfg_path: str, project: str | None, fmt: str) -> None:
    """Display uptime statistics."""
    cfg = load_config(cfg_path)
    history_path = getattr(cfg, "history_path", ".depwatch_history.json")

    if project:
        entry = compute_uptime(history_path, project)
        entries = [entry] if entry else []
    else:
        entries = compute_all_uptime(history_path)

    if fmt == "json":
        data = [
            {
                "project": e.project,
                "total_runs": e.total_runs,
                "clean_runs": e.clean_runs,
                "uptime_pct": e.uptime_pct,
                "current_streak": e.current_streak,
                "longest_streak": e.longest_streak,
                "last_clean": e.last_clean.isoformat() if e.last_clean else None,
            }
            for e in entries
        ]
        click.echo(json.dumps(data, indent=2))
    else:
        click.echo(format_uptime_report(entries))


@uptime_cmd.command("check")
@click.option("--config", "cfg_path", default="depwatch.toml", show_default=True)
@click.option("--min-uptime", "min_uptime", type=float, default=80.0, show_default=True,
              help="Fail if any project's uptime% is below this threshold.")
def check_cmd(cfg_path: str, min_uptime: float) -> None:
    """Exit non-zero if any project falls below the minimum uptime threshold."""
    cfg = load_config(cfg_path)
    history_path = getattr(cfg, "history_path", ".depwatch_history.json")
    entries = compute_all_uptime(history_path)

    failures = [e for e in entries if e.uptime_pct < min_uptime]
    if failures:
        for e in failures:
            click.echo(
                f"FAIL  {e.project}: {e.uptime_pct:.1f}% uptime (threshold {min_uptime:.1f}%)",
                err=True,
            )
        raise SystemExit(1)

    click.echo(f"All projects meet the {min_uptime:.1f}% uptime threshold.")
