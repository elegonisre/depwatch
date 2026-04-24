"""CLI commands for package ownership management."""
from __future__ import annotations

import click

from depwatch.ownership import (
    DEFAULT_OWNERSHIP_FILE,
    assign_owner,
    get_owners,
    load_ownership,
    packages_for_owner,
    remove_owner,
    save_ownership,
)


@click.group("ownership")
def ownership_cmd() -> None:
    """Manage package ownership assignments."""


@ownership_cmd.command("assign")
@click.argument("project")
@click.argument("package")
@click.argument("owner")
@click.option("--file", "filepath", default=str(DEFAULT_OWNERSHIP_FILE), show_default=True)
def assign_cmd(project: str, package: str, owner: str, filepath: str) -> None:
    """Assign OWNER to PACKAGE in PROJECT."""
    from pathlib import Path
    path = Path(filepath)
    data = load_ownership(path)
    assign_owner(data, project, package, owner)
    save_ownership(data, path)
    click.echo(f"Assigned '{owner}' to {project}/{package}.")


@ownership_cmd.command("remove")
@click.argument("project")
@click.argument("package")
@click.argument("owner")
@click.option("--file", "filepath", default=str(DEFAULT_OWNERSHIP_FILE), show_default=True)
def remove_cmd(project: str, package: str, owner: str, filepath: str) -> None:
    """Remove OWNER from PACKAGE in PROJECT."""
    from pathlib import Path
    path = Path(filepath)
    data = load_ownership(path)
    remove_owner(data, project, package, owner)
    save_ownership(data, path)
    click.echo(f"Removed '{owner}' from {project}/{package}.")


@ownership_cmd.command("list")
@click.argument("project")
@click.argument("package")
@click.option("--file", "filepath", default=str(DEFAULT_OWNERSHIP_FILE), show_default=True)
def list_cmd(project: str, package: str, filepath: str) -> None:
    """List owners of PACKAGE in PROJECT."""
    from pathlib import Path
    data = load_ownership(Path(filepath))
    owners = get_owners(data, project, package)
    if owners:
        for o in owners:
            click.echo(o)
    else:
        click.echo("No owners assigned.")


@ownership_cmd.command("by-owner")
@click.argument("owner")
@click.option("--project", default=None, help="Filter to a specific project.")
@click.option("--file", "filepath", default=str(DEFAULT_OWNERSHIP_FILE), show_default=True)
def by_owner_cmd(owner: str, project: str | None, filepath: str) -> None:
    """Show all packages owned by OWNER."""
    from pathlib import Path
    data = load_ownership(Path(filepath))
    result = packages_for_owner(data, owner, project)
    if not result:
        click.echo(f"No packages found for owner '{owner}'.")
        return
    for proj, pkgs in result.items():
        click.echo(f"{proj}: {', '.join(pkgs)}")
