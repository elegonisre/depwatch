"""CLI commands for pin suggestions."""
import click
from depwatch.config import load_config
from depwatch.checker import check_dependencies
from depwatch.pin import suggest_pins, format_suggestions


@click.group("pin")
def pin_cmd():
    """Dependency pinning suggestions."""


@pin_cmd.command("suggest")
@click.option("--config", default="depwatch.toml", show_default=True)
@click.option("--pin-current", is_flag=True, default=False, help="Also suggest pinning up-to-date deps.")
@click.option("--project", default=None, help="Limit to a specific project.")
def suggest_cmd(config, pin_current, project):
    """Show upgrade/pin suggestions for outdated dependencies."""
    cfg = load_config(config)
    projects = cfg.projects
    if project:
        projects = [p for p in projects if p.name == project]
        if not projects:
            click.echo(f"Project '{project}' not found.")
            raise SystemExit(1)

    all_statuses = []
    for proj in projects:
        statuses = check_dependencies(proj.name, proj.requirements)
        all_statuses.extend(statuses)

    suggestions = suggest_pins(all_statuses, pin_to_latest=pin_current)
    click.echo(format_suggestions(suggestions))


@pin_cmd.command("list")
@click.option("--config", default="depwatch.toml", show_default=True)
def list_cmd(config):
    """List only packages that need upgrading (pin specs)."""
    cfg = load_config(config)
    all_statuses = []
    for proj in cfg.projects:
        all_statuses.extend(check_dependencies(proj.name, proj.requirements))

    suggestions = suggest_pins(all_statuses)
    if not suggestions:
        click.echo("All dependencies are up to date.")
    else:
        for s in suggestions:
            click.echo(s.pin_spec)
