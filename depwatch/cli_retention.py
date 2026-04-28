"""CLI commands for the retention policy feature."""
from __future__ import annotations

import click

from depwatch.retention import apply_retention, format_retention_report
from depwatch.history import _HISTORY_FILE


@click.group("retention")
def retention_cmd() -> None:
    """Manage history retention policy."""


@retention_cmd.command("prune")
@click.option(
    "--max-days",
    default=90,
    show_default=True,
    type=click.IntRange(min=1),
    help="Remove history runs older than this many days.",
)
@click.option(
    "--history-file",
    default=None,
    type=click.Path(),
    help="Path to the history JSON file (defaults to depwatch_history.json).",
)
@click.option(
    "--quiet",
    is_flag=True,
    default=False,
    help="Suppress output; exit code reflects whether anything was removed.",
)
def prune_cmd(
    max_days: int,
    history_file: str | None,
    quiet: bool,
) -> None:
    """Prune history entries older than MAX_DAYS days."""
    from pathlib import Path

    hf = Path(history_file) if history_file else _HISTORY_FILE
    result = apply_retention(max_days=max_days, history_file=hf)

    if not quiet:
        click.echo(format_retention_report(result))

    if result.removed > 0:
        raise SystemExit(0)
