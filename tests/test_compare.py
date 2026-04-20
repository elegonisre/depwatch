"""Tests for depwatch.compare."""
import pytest
from depwatch.checker import DependencyStatus
from depwatch.compare import compare_projects, format_compare_report


def _s(pkg, installed, latest, outdated=False):
    return DependencyStatus(
        package=pkg,
        installed_version=installed,
        latest_version=latest,
        is_outdated=outdated,
    )


A = [
    _s("requests", "2.28.0", "2.31.0", True),
    _s("flask", "2.3.0", "2.3.0", False),
]

B = [
    _s("requests", "2.31.0", "2.31.0", False),
    _s("django", "4.2.0", "4.2.1", True),
]


def test_only_in_a():
    entries = compare_projects("alpha", A, "beta", B)
    flask_entry = next(e for e in entries if e.package == "flask")
    assert flask_entry.only_in_a
    assert not flask_entry.only_in_b


def test_only_in_b():
    entries = compare_projects("alpha", A, "beta", B)
    django_entry = next(e for e in entries if e.package == "django")
    assert django_entry.only_in_b
    assert not django_entry.only_in_a


def test_version_differs():
    entries = compare_projects("alpha", A, "beta", B)
    req_entry = next(e for e in entries if e.package == "requests")
    assert req_entry.version_differs
    assert req_entry.project_a == "2.28.0"
    assert req_entry.project_b == "2.31.0"


def test_same_version():
    same_b = [_s("flask", "2.3.0", "2.3.0")]
    entries = compare_projects("alpha", A, "beta", same_b)
    flask_entry = next(e for e in entries if e.package == "flask")
    assert not flask_entry.version_differs
    assert not flask_entry.only_in_a
    assert not flask_entry.only_in_b


def test_all_packages_covered():
    entries = compare_projects("alpha", A, "beta", B)
    pkgs = {e.package for e in entries}
    assert pkgs == {"requests", "flask", "django"}


def test_format_report_contains_names():
    entries = compare_projects("alpha", A, "beta", B)
    report = format_compare_report("alpha", "beta", entries)
    assert "alpha" in report
    assert "beta" in report


def test_format_report_shows_diff():
    entries = compare_projects("alpha", A, "beta", B)
    report = format_compare_report("alpha", "beta", entries)
    assert "2.28.0" in report
    assert "2.31.0" in report
