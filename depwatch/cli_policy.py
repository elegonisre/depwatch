"""CLI commands for policy enforcement."""
import json
import sys
import click
from depwatch.config import load_config
from depwatch.checker import check_dependencies
from depwatch.policy import Policy, evaluate_policy


@click.group("policy")
def policy_cmd():
    """Enforce dependency policies."""


@policy_cmd.command("check")
@click.option("--config", "cfg_path", default="depwatch.toml", show_default=True)
@click.option("--max-outdated", type=int, default=None, help="Max allowed outdated deps.")
@click.option("--max-ratio", type=float, default=None, help="Max outdated ratio (0-1).")
@click.option("--block-major-behind", type=int, default=None, help="Block if N+ majors behind.")
@click.option("--format", "fmt", type=click.Choice(["text", "json"]), default="text")
@click.pass_context
def check_cmd(ctx, cfg_path, max_outdated, max_ratio, block_major_behind, fmt):
    """Run policy check against all configured projects."""
    cfg = load_config(cfg_path)
    policy = Policy(
        max_outdated=max_outdated,
        max_outdated_ratio=max_ratio,
        block_major_behind=block_major_behind,
    )

    all_statuses = []
    for project in cfg.projects:
        all_statuses.extend(check_dependencies(project.requirements))

    result = evaluate_policy(policy, all_statuses)

    if fmt == "json":
        click.echo(json.dumps({"passed": result.passed, "reason": result.reason}))
    else:
        status_str = click.style("PASS", fg="green") if result.passed else click.style("FAIL", fg="red")
        click.echo(f"Policy: [{status_str}] {result.reason}")

    if not result.passed:
        sys.exit(1)
