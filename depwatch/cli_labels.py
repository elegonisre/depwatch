"""CLI commands for managing dependency labels."""
from __future__ import annotations

import click

from depwatch.labels import (
    add_label,
    filter_by_label,
    get_labels,
    load_labels,
    remove_label,
)


@click.group("labels")
def labels_cmd() -> None:
    """Manage custom labels attached to packages."""


@labels_cmd.command("add")
@click.argument("package")
@click.argument("label")
def add_cmd(package: str, label: str) -> None:
    """Attach LABEL to PACKAGE."""
    add_label(package, label)
    click.echo(f"Label '{label}' added to '{package}'.")


@labels_cmd.command("remove")
@click.argument("package")
@click.argument("label")
def remove_cmd(package: str, label: str) -> None:
    """Remove LABEL from PACKAGE."""
    remove_label(package, label)
    click.echo(f"Label '{label}' removed from '{package}'.")


@labels_cmd.command("list")
@click.argument("package", required=False)
def list_cmd(package: str | None) -> None:
    """List labels. If PACKAGE given, show only its labels."""
    if package:
        tags = get_labels(package)
        if tags:
            click.echo(f"{package}: {', '.join(tags)}")
        else:
            click.echo(f"No labels for '{package}'.")
    else:
        all_labels = load_labels()
        if not all_labels:
            click.echo("No labels defined.")
            return
        for pkg, tags in sorted(all_labels.items()):
            click.echo(f"{pkg}: {', '.join(tags)}")


@labels_cmd.command("filter")
@click.argument("label")
@click.argument("packages", nargs=-1, required=True)
def filter_cmd(label: str, packages: tuple[str, ...]) -> None:
    """Print which PACKAGES carry LABEL."""
    matched = filter_by_label(list(packages), label)
    if matched:
        for p in matched:
            click.echo(p)
    else:
        click.echo(f"No packages matched label '{label}'.")
