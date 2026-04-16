"""CLI sub-command for the digest feature, registered in cli.py."""
from __future__ import annotations

import click

from depwatch.digest import build_digest
from depwatch.config import load_config
from depwatch.notifier import EmailChannel, LogChannel, NotifierConfig, notify_all
from depwatch.checker import DependencyStatus


@click.command("digest")
@click.option("--config", "config_path", default="depwatch.toml", show_default=True)
@click.option("--days", default=7, show_default=True, help="Look-back window in days.")
@click.option("--history", "history_path", default="depwatch_history.jsonl", show_default=True)
@click.option("--send", is_flag=True, default=False, help="Send digest via configured alert channel.")
def digest_cmd(config_path: str, days: int, history_path: str, send: bool) -> None:
    """Print (and optionally send) a summary digest of recent dependency health."""
    text = build_digest(history_path, days=days)
    click.echo(text)

    if send:
        try:
            cfg = load_config(config_path)
        except FileNotFoundError:
            raise click.ClickException(f"Config file not found: {config_path}")

        if cfg.alert is None:
            raise click.ClickException("No [alert] section in config; cannot send digest.")

        channels = [
            EmailChannel(config=cfg.alert),
            LogChannel(level="info"),
        ]
        notifier_cfg = NotifierConfig(channels=channels)
        # Represent digest as a single synthetic status so channels fire.
        synthetic = [
            DependencyStatus(
                package="digest",
                current="",
                latest="see digest",
                is_outdated=True,
            )
        ]
        fired = notify_all("digest", synthetic, notifier_cfg)
        click.echo(f"Digest sent via {fired} channel(s).")
