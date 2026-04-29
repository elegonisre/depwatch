"""CLI commands for cadence analysis."""
import json
import click

from depwatch.cadence import compute_cadence, format_cadence_report


@click.group("cadence")
def cadence_cmd():
    """Analyse how regularly projects are checked."""


@cadence_cmd.command("show")
@click.option("--history", default="depwatch_history.json", show_default=True,
              help="Path to history file.")
@click.option("--format", "fmt", type=click.Choice(["text", "json"]), default="text",
              show_default=True)
@click.option("--min-runs", default=1, show_default=True,
              help="Only show projects with at least this many runs.")
def show_cmd(history: str, fmt: str, min_runs: int):
    """Show cadence statistics for all projects."""
    entries = compute_cadence(history)
    entries = [e for e in entries if e.run_count >= min_runs]

    if fmt == "json":
        data = [
            {
                "project": e.project,
                "run_count": e.run_count,
                "first_seen": e.first_seen.isoformat() if e.first_seen else None,
                "last_seen": e.last_seen.isoformat() if e.last_seen else None,
                "avg_interval_hours": round(e.avg_interval_hours, 2)
                if e.avg_interval_hours is not None
                else None,
                "regularity_label": e.regularity_label,
            }
            for e in entries
        ]
        click.echo(json.dumps(data, indent=2))
    else:
        click.echo(format_cadence_report(entries))
