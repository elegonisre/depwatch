"""Module for checking outdated Python dependencies using PyPI."""

import requests
from dataclasses import dataclass
from typing import Optional

PYPI_URL = "https://pypi.org/pypi/{package}/json"


@dataclass
class DependencyStatus:
    name: str
    current_version: str
    latest_version: str
    is_outdated: bool
    error: Optional[str] = None


def get_latest_version(package_name: str) -> Optional[str]:
    """Fetch the latest version of a package from PyPI."""
    try:
        response = requests.get(PYPI_URL.format(package=package_name), timeout=5)
        response.raise_for_status()
        data = response.json()
        return data["info"]["version"]
    except requests.RequestException as e:
        raise RuntimeError(f"Failed to fetch version for '{package_name}': {e}")


def check_dependency(name: str, current_version: str) -> DependencyStatus:
    """Check if a single dependency is outdated."""
    try:
        latest = get_latest_version(name)
        outdated = latest != current_version
        return DependencyStatus(
            name=name,
            current_version=current_version,
            latest_version=latest,
            is_outdated=outdated,
        )
    except RuntimeError as e:
        return DependencyStatus(
            name=name,
            current_version=current_version,
            latest_version="unknown",
            is_outdated=False,
            error=str(e),
        )


def check_dependencies(deps: dict[str, str]) -> list[DependencyStatus]:
    """Check a dict of {package: current_version} for outdated packages."""
    return [check_dependency(name, version) for name, version in deps.items()]
