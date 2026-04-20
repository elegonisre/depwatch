"""CLI commands for the audit log feature."""
from __future__ import annotations

import json
from pathlib import Path

import click

from depwatch.audit import (
    DEFAULT_AUDIT_FILE,
    format_audit_log,
    load_audit_log,
    record_audit,
)
from depwatch.config import load_config
from depwatch.checker import check_dependencies


@click.group("audit")
def audit_cmd():
    """Audit log commands."""


@audit_cmd.command("log")
@click.option("--file", "audit_file", default=str(DEFAULT_AUDIT_FILE), show_default=True)
@click.option("--json", "as_json", is_flag=True, default=False)
def log_cmd(audit_file: str, as_json: bool):
    """Display the audit log."""
    entries = load_audit_log(Path(audit_file))
    if as_json:
        data = [
            {
                "timestamp": e.timestamp,
                "project": e.project,
                "total": e.total,
                "outdated": e.outdated,
                "triggered_by": e.triggered_by,
                "tags": e.tags,
                "note": e.note,
            }
            for e in entries
        ]
        click.echo(json.dumps(data, indent=2))
    else:
        click.echo(format_audit_log(entries))


@audit_cmd.command("record")
@click.option("--config", "cfg_path", default="depwatch.toml", show_default=True)
@click.option("--triggered-by", default="cli", show_default=True)
@click.option("--tag", "tags", multiple=True)
@click.option("--note", default=None)
@click.option("--file", "audit_file", default=str(DEFAULT_AUDIT_FILE), show_default=True)
def record_cmd(cfg_path: str, triggered_by: str, tags: tuple, note: str | None, audit_file: str):
    """Run checks and record results to the audit log."""
    cfg = load_config(Path(cfg_path))
    for project in cfg.projects:
        statuses = check_dependencies(project.requirements)
        total = len(statuses)
        outdated = sum(1 for s in statuses if s.is_outdated)
        entry = record_audit(
            project=project.name,
            total=total,
            outdated=outdated,
            triggered_by=triggered_by,
            tags=list(tags),
            note=note,
            audit_file=Path(audit_file),
        )
        click.echo(f"[{entry.timestamp}] {project.name}: {outdated}/{total} outdated recorded.")
