"""CLI commands for dependency health scoring."""
import click
from depwatch.config import load_config
from depwatch.checker import check_dependencies
from depwatch.score import score_all, format_scores
import json


@click.group("score")
def score_cmd():
    """Health score commands."""


@score_cmd.command("show")
@click.option("--config", default="depwatch.toml", show_default=True)
@click.option("--json", "as_json", is_flag=True, default=False)
def show_cmd(config, as_json):
    """Show health scores for all configured projects."""
    cfg = load_config(config)
    results = {}
    for project in cfg.projects:
        results[project.name] = check_dependencies(project.requirements)
    scores = score_all(results)
    if as_json:
        data = [
            {
                "project": s.project,
                "score": s.score,
                "grade": s.grade,
                "total": s.total,
                "outdated": s.outdated,
            }
            for s in scores
        ]
        click.echo(json.dumps(data, indent=2))
    else:
        click.echo(format_scores(scores))


@score_cmd.command("check")
@click.option("--config", default="depwatch.toml", show_default=True)
@click.option("--min-score", default=80.0, show_default=True, type=float)
def check_cmd(config, min_score):
    """Exit non-zero if any project score is below threshold."""
    cfg = load_config(config)
    results = {}
    for project in cfg.projects:
        results[project.name] = check_dependencies(project.requirements)
    scores = score_all(results)
    failing = [s for s in scores if s.score < min_score]
    if failing:
        for s in failing:
            click.echo(f"FAIL {s.project}: {s.score}% (min {min_score}%)")
        raise SystemExit(1)
    click.echo("All projects meet the minimum score threshold.")
