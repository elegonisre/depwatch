"""CLI commands for grouped dependency views."""
import json
import click
from depwatch.config import load_config
from depwatch.checker import check_dependencies
from depwatch.groupby import group_by_project, group_by_status, group_by_major_version_gap, summary


@click.group("group")
def group_cmd():
    """View dependencies grouped by various attributes."""


@group_cmd.command("by-project")
@click.option("--config", "cfg_path", default="depwatch.toml", show_default=True)
def by_project_cmd(cfg_path: str):
    """Show outdated counts grouped by project."""
    cfg = load_config(cfg_path)
    all_statuses = []
    for project in cfg.projects:
        all_statuses.extend(check_dependencies(project))
    groups = group_by_project(all_statuses)
    for project, statuses in sorted(groups.items()):
        s = summary(statuses)
        click.echo(f"{project}: {s['outdated']}/{s['total']} outdated")


@group_cmd.command("by-status")
@click.option("--config", "cfg_path", default="depwatch.toml", show_default=True)
@click.option("--json", "as_json", is_flag=True, default=False)
def by_status_cmd(cfg_path: str, as_json: bool):
    """Show dependencies split into outdated / up-to-date."""
    cfg = load_config(cfg_path)
    all_statuses = []
    for project in cfg.projects:
        all_statuses.extend(check_dependencies(project))
    groups = group_by_status(all_statuses)
    if as_json:
        out = {k: [s.package for s in v] for k, v in groups.items()}
        click.echo(json.dumps(out, indent=2))
    else:
        for bucket, statuses in groups.items():
            click.echo(f"[{bucket}]")
            for s in statuses:
                click.echo(f"  {s.project}/{s.package} {s.current_version} -> {s.latest_version}")


@group_cmd.command("by-gap")
@click.option("--config", "cfg_path", default="depwatch.toml", show_default=True)
def by_gap_cmd(cfg_path: str):
    """Show outdated dependencies grouped by major version gap."""
    cfg = load_config(cfg_path)
    all_statuses = []
    for project in cfg.projects:
        all_statuses.extend(check_dependencies(project))
    groups = group_by_major_version_gap(all_statuses)
    labels = {"none": "same major", "one": "1 major behind", "multiple": "2+ majors behind"}
    for key, label in labels.items():
        pkgs = [s.package for s in groups[key] if s.is_outdated]
        if pkgs:
            click.echo(f"{label}: {', '.join(pkgs)}")
