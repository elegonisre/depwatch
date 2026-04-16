"""Configuration loader for depwatch."""

from __future__ import annotations

import tomllib
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

from depwatch.alerts import AlertConfig


@dataclass
class ProjectConfig:
    name: str
    requirements: str  # path to requirements file


@dataclass
class DepwatchConfig:
    projects: List[ProjectConfig] = field(default_factory=list)
    alert: Optional[AlertConfig] = None


def load_config(path: str | Path = "depwatch.toml") -> DepwatchConfig:
    """Load and parse a depwatch.toml configuration file."""
    config_path = Path(path)
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    with open(config_path, "rb") as f:
        data = tomllib.load(f)

    projects = [
        ProjectConfig(name=p["name"], requirements=p["requirements"])
        for p in data.get("projects", [])
    ]

    alert_cfg = None
    if "alert" in data:
        a = data["alert"]
        alert_cfg = AlertConfig(
            smtp_host=a["smtp_host"],
            smtp_port=a.get("smtp_port", 587),
            sender=a["sender"],
            recipients=a["recipients"],
            username=a.get("username", ""),
            password=a.get("password", ""),
            use_tls=a.get("use_tls", True),
        )

    return DepwatchConfig(projects=projects, alert=alert_cfg)
