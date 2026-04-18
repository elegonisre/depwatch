"""CLI commands for managing the depwatch ignore list."""
import click
from pathlib import Path
from depwatch.ignore import (
    load_ignore_list,
    add_to_ignore,
    remove_from_ignore,
    DEFAULT_IGNORE_FILE,
)


@click.group("ignore")
def ignore_cmd():
    """Manage the ignored-dependencies list."""


@ignore_cmd.command("add")
@click.argument("package")
@click.option("--file", "ignore_file", default=str(DEFAULT_IGNORE_FILE), show_default=True)
def add_cmd(package: str, ignore_file: str):
    """Add PACKAGE to the ignore list."""
    result = add_to_ignore(package, Path(ignore_file))
    click.echo(f"Added '{package}'. Ignored packages: {', '.join(result)}")


@ignore_cmd.command("remove")
@click.argument("package")
@click.option("--file", "ignore_file", default=str(DEFAULT_IGNORE_FILE), show_default=True)
def remove_cmd(package: str, ignore_file: str):
    """Remove PACKAGE from the ignore list."""
    result = remove_from_ignore(package, Path(ignore_file))
    if result:
        click.echo(f"Removed '{package}'. Remaining: {', '.join(result)}")
    else:
        click.echo(f"Removed '{package}'. Ignore list is now empty.")


@ignore_cmd.command("list")
@click.option("--file", "ignore_file", default=str(DEFAULT_IGNORE_FILE), show_default=True)
def list_cmd(ignore_file: str):
    """Show all currently ignored packages."""
    packages = load_ignore_list(Path(ignore_file))
    if not packages:
        click.echo("No packages are currently ignored.")
    else:
        for pkg in packages:
            click.echo(pkg)
