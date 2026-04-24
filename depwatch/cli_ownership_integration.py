"""Register ownership commands into the main depwatch CLI."""
from __future__ import annotations

import click

from depwatch.cli_ownership import ownership_cmd


def register(cli: click.Group) -> None:
    """Attach the ownership command group to *cli*."""
    cli.add_command(ownership_cmd)
