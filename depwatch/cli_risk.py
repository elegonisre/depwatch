"""CLI commands for dependency risk assessment."""
import click
import json
from depwatch.config import load_config
from depwatch.checker import check_dependencies
from depwatch.risk import assess_risk, format_risk_report


@click.group("risk")
def risk_cmd():
    """Assess risk level of outdated dependencies."""


@risk_cmd.command("show")
@click.option("--config", "config_path", default="depwatch.toml", show_default=True)
@click.option("--project", default=None, help="Filter to a single project.")
@click.option("--min-label", default=None, type=click.Choice(["low", "medium", "high", "critical"]), help="Minimum risk label to show.")
@click.option("--format", "fmt", default="text", type=click.Choice(["text", "json"]), show_default=True)
def show_cmd(config_path, project, min_label, fmt):
    """Show risk assessment for outdated dependencies."""
    cfg = load_config(config_path)
    label_order = ["low", "medium", "high", "critical"]
    min_idx = label_order.index(min_label) if min_label else 0

    all_entries = []
    for proj in cfg.projects:
        if project and proj.name != project:
            continue
        statuses = check_dependencies(proj.requirements)
        entries = assess_risk(proj.name, statuses)
        if min_label:
            entries = [e for e in entries if label_order.index(e.risk_label) >= min_idx]
        all_entries.extend(entries)

    if fmt == "json":
        data = [
            {
                "project": e.project,
                "package": e.package,
                "current_version": e.current_version,
                "latest_version": e.latest_version,
                "major_gap": e.major_gap,
                "minor_gap": e.minor_gap,
                "risk_score": e.risk_score,
                "risk_label": e.risk_label,
            }
            for e in all_entries
        ]
        click.echo(json.dumps(data, indent=2))
    else:
        click.echo(format_risk_report(all_entries))
