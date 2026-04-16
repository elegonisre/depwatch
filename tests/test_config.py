"""Tests for depwatch.config."""

import textwrap
from pathlib import Path

import pytest

from depwatch.config import load_config


TOML_FULL = textwrap.dedent("""\
    [[projects]]
    name = "my-app"
    requirements = "requirements.txt"

    [[projects]]
    name = "svc"
    requirements = "svc/requirements.txt"

    [alert]
    smtp_host = "smtp.example.com"
    smtp_port = 587
    sender = "a@example.com"
    recipients = ["b@example.com"]
    use_tls = true
""")

TOML_NO_ALERT = textwrap.dedent("""\
    [[projects]]
    name = "my-app"
    requirements = "requirements.txt"
""")


def test_load_config_full(tmp_path: Path):
    cfg_file = tmp_path / "depwatch.toml"
    cfg_file.write_text(TOML_FULL)

    cfg = load_config(cfg_file)

    assert len(cfg.projects) == 2
    assert cfg.projects[0].name == "my-app"
    assert cfg.projects[1].requirements == "svc/requirements.txt"
    assert cfg.alert is not None
    assert cfg.alert.smtp_host == "smtp.example.com"
    assert cfg.alert.recipients == ["b@example.com"]


def test_load_config_no_alert(tmp_path: Path):
    cfg_file = tmp_path / "depwatch.toml"
    cfg_file.write_text(TOML_NO_ALERT)

    cfg = load_config(cfg_file)
    assert len(cfg.projects) == 1
    assert cfg.alert is None


def test_load_config_missing_file(tmp_path: Path):
    with pytest.raises(FileNotFoundError):
        load_config(tmp_path / "nonexistent.toml")
