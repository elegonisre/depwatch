"""Register dep-age commands into the main CLI."""
from __future__ import annotations

import click

from depwatch.cli_dependency_age import dep_age_cmd


def register(cli: click.Group) -> None:
    """Attach the dep-age command group to *cli*."""
    cli.add_command(dep_age_cmd)
