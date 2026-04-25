"""Tests for depwatch.dependency_graph."""
from __future__ import annotations

from typing import List

from depwatch.checker import DependencyStatus
from depwatch.dependency_graph import (
    DependencyGraph,
    build_graph,
    format_graph_report,
    shared_outdated,
)


def _s(pkg: str, current: str, latest: str, outdated: bool) -> DependencyStatus:
    return DependencyStatus(
        package=pkg,
        current_version=current,
        latest_version=latest,
        is_outdated=outdated,
    )


_PROJECT_A = [
    _s("requests", "2.28.0", "2.31.0", True),
    _s("click", "8.1.0", "8.1.0", False),
]

_PROJECT_B = [
    _s("requests", "2.28.0", "2.31.0", True),
    _s("flask", "2.3.0", "3.0.0", True),
]

_PROJECT_C = [
    _s("click", "8.1.0", "8.1.0", False),
]


def test_build_graph_node_count() -> None:
    graph = build_graph({"a": _PROJECT_A, "b": _PROJECT_B})
    assert len(graph.nodes) == 4


def test_build_graph_shared_packages() -> None:
    graph = build_graph({"a": _PROJECT_A, "b": _PROJECT_B})
    assert "requests" in graph.shared_packages
    assert graph.shared_packages["requests"] == {"a", "b"}


def test_build_graph_dependents_populated() -> None:
    graph = build_graph({"a": _PROJECT_A, "b": _PROJECT_B})
    req_nodes = [n for n in graph.nodes if n.package == "requests"]
    assert len(req_nodes) == 2
    for node in req_nodes:
        assert len(node.dependents) == 1  # each sees the other project


def test_build_graph_no_dependents_when_unique() -> None:
    graph = build_graph({"a": _PROJECT_A, "b": _PROJECT_B})
    flask_node = next(n for n in graph.nodes if n.package == "flask")
    assert flask_node.dependents == []


def test_shared_outdated_returns_only_multi_project() -> None:
    graph = build_graph({"a": _PROJECT_A, "b": _PROJECT_B})
    result = shared_outdated(graph)
    assert "requests" in result
    assert set(result["requests"]) == {"a", "b"}
    # flask is outdated but only in project b
    assert "flask" not in result


def test_shared_outdated_empty_when_no_overlap() -> None:
    graph = build_graph({"a": _PROJECT_A, "c": _PROJECT_C})
    result = shared_outdated(graph)
    # click is shared but not outdated; requests only in a
    assert result == {}


def test_format_graph_report_contains_header() -> None:
    graph = build_graph({"a": _PROJECT_A, "b": _PROJECT_B})
    report = format_graph_report(graph)
    assert "Dependency Graph Report" in report


def test_format_graph_report_shows_shared_outdated() -> None:
    graph = build_graph({"a": _PROJECT_A, "b": _PROJECT_B})
    report = format_graph_report(graph)
    assert "requests" in report


def test_format_graph_report_no_shared_message() -> None:
    graph = build_graph({"a": _PROJECT_A, "c": _PROJECT_C})
    report = format_graph_report(graph)
    assert "No packages are outdated across multiple projects" in report


def test_format_graph_report_totals() -> None:
    graph = build_graph({"a": _PROJECT_A, "b": _PROJECT_B})
    report = format_graph_report(graph)
    assert "Total nodes: 4" in report
