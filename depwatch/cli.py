"""CLI entry point for depwatch."""

import logging
import click

from depwatch.config import load_config
from depwatch.checker import check_dependencies
from depwatch.alerts import send_email_alert
from depwatch.reporter import generate_report
from depwatch.scheduler import run_scheduler

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger(__name__)


@click.group()
def cli() -> None:
    """depwatch — monitor outdated Python dependencies."""


@cli.command("check")
@click.option("--config", default="depwatch.toml", show_default=True, help="Config file path.")
@click.option("--format", "fmt", default="text", type=click.Choice(["text", "json"]), show_default=True)
@click.option("--alert", is_flag=True, default=False, help="Send email alert if outdated deps found.")
def check_cmd(config: str, fmt: str, alert: bool) -> None:
    """Check dependencies for all configured projects."""
    cfg = load_config(config)
    for project in cfg.projects:
        statuses = check_dependencies(project.dependencies)
        report = generate_report(project.name, statuses, fmt=fmt)
        click.echo(report)
        if alert and cfg.alert:
            send_email_alert(cfg.alert, project.name, statuses)


@cli.command("watch")
@click.option("--config", default="depwatch.toml", show_default=True, help="Config file path.")
@click.option("--interval", default="6h", show_default=True, help="Check interval, e.g. 30m, 6h.")
@click.option("--format", "fmt", default="text", type=click.Choice(["text", "json"]), show_default=True)
@click.option("--alert", is_flag=True, default=False, help="Send email alerts when outdated deps found.")
def watch_cmd(config: str, interval: str, fmt: str, alert: bool) -> None:
    """Continuously watch dependencies at a set interval."""
    cfg = load_config(config)

    def _run_check() -> None:
        for project in cfg.projects:
            statuses = check_dependencies(project.dependencies)
            report = generate_report(project.name, statuses, fmt=fmt)
            click.echo(report)
            if alert and cfg.alert:
                send_email_alert(cfg.alert, project.name, statuses)

    click.echo(f"Starting watch mode (interval={interval}). Press Ctrl+C to stop.")
    try:
        run_scheduler(_run_check, interval)
    except KeyboardInterrupt:
        click.echo("\nWatch stopped.")


if __name__ == "__main__":
    cli()
