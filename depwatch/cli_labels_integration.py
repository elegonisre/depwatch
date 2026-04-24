"""Wire labels_cmd into the top-level depwatch CLI.

Import and register this module in cli.py::

    from depwatch.cli_labels_integration import register
    register(cli)
"""
from __future__ import annotations

import click

from depwatch.cli_labels import labels_cmd
from depwatch.checker import check_dependencies
from depwatch.config import load_config
from depwatch.labels import filter_by_label, load_labels


def register(cli: click.Group) -> None:
    """Attach the *labels* command group to *cli*."""
    cli.add_command(labels_cmd)


@labels_cmd.command("scan")
@click.argument("label")
@click.option("--config", "config_path", default="depwatch.toml", show_default=True)
def scan_cmd(label: str, config_path: str) -> None:
    """Run a dependency check filtered to packages carrying LABEL."""
    cfg = load_config(config_path)
    all_labels = load_labels()

    for project in cfg.projects:
        packages = [dep for dep in project.dependencies]
        tagged = filter_by_label(packages, label)
        if not tagged:
            click.echo(f"[{project.name}] No packages with label '{label}'.")
            continue

        click.echo(f"[{project.name}] Checking {len(tagged)} package(s) labelled '{label}'...")
        statuses = check_dependencies(tagged)
        for s in statuses:
            indicator = "outdated" if s.is_outdated else "up-to-date"
            click.echo(
                f"  {s.package}: {s.current_version} -> {s.latest_version} [{indicator}]"
            )
