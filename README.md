# depwatch

> CLI tool that monitors outdated dependencies across multiple Python projects and sends alerts.

---

## Installation

```bash
pip install depwatch
```

Or install from source:

```bash
git clone https://github.com/yourname/depwatch.git && cd depwatch && pip install .
```

---

## Usage

Point `depwatch` at one or more project directories and let it check for outdated dependencies:

```bash
# Check a single project
depwatch check /path/to/my-project

# Watch multiple projects and send alerts
depwatch watch /projects/app1 /projects/app2 --alert email

# Output a report in JSON format
depwatch check . --format json
```

### Configuration

Create a `depwatch.toml` in your home or project directory to set defaults:

```toml
[alerts]
method = "slack"
webhook_url = "https://hooks.slack.com/your-webhook"

[watch]
interval = 3600  # check every hour
```

---

## Features

- Scans `requirements.txt`, `pyproject.toml`, and `setup.cfg`
- Supports multiple alert channels (email, Slack, webhook)
- Scheduled background monitoring with `depwatch watch`
- JSON, table, and plain-text output formats

---

## License

MIT © 2024 Your Name