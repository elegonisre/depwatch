"""CLI sub-commands for filtered dependency views."""
from __future__ import annotations
import click
from depwatch.config import load_config
from depwatch.checker import check_dependencies
from depwatch.filter import (
    filter_outdated,
    filter_min_versions_behind,
    apply_ignore_list,
)
from depwatch.reporter import generate_report


@click.group("filter")
def filter_cmd():
    """Filter and inspect dependency results."""


@filter_cmd.command("outdated")
@click.option("--config", "config_path", default="depwatch.toml", show_default=True)
@click.option("--format", "fmt", default="text", type=click.Choice(["text", "json"]), show_default=True)
@click.option("--ignore", multiple=True, help="Package names to ignore (repeatable).")
def outdated_cmd(config_path: str, fmt: str, ignore: tuple):
    """Show only outdated dependencies across all projects."""
    cfg = load_config(config_path)
    for project in cfg.projects:
        statuses = check_dependencies(project.requirements_file)
        statuses = apply_ignore_list(statuses, list(ignore))
        statuses = filter_outdated(statuses)
        click.echo(generate_report(project.name, statuses, fmt))


@filter_cmd.command("major-behind")
@click.argument("min_behind", type=int, default=1)
@click.option("--config", "config_path", default="depwatch.toml", show_default=True)
@click.option("--format", "fmt", default="text", type=click.Choice(["text", "json"]), show_default=True)
def major_behind_cmd(min_behind: int, config_path: str, fmt: str):
    """Show dependencies at least MIN_BEHIND major versions behind."""
    cfg = load_config(config_path)
    for project in cfg.projects:
        statuses = check_dependencies(project.requirements_file)
        statuses = filter_min_versions_behind(statuses, min_behind)
        if statuses:
            click.echo(generate_report(project.name, statuses, fmt))
        else:
            click.echo(f"[{project.name}] No dependencies {min_behind}+ major version(s) behind.")
