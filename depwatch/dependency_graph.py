"""Dependency graph: build and analyse inter-project dependency relationships."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Set

from depwatch.checker import DependencyStatus


@dataclass
class GraphNode:
    project: str
    package: str
    current_version: str
    latest_version: str
    is_outdated: bool
    dependents: List[str] = field(default_factory=list)  # other projects using same package


@dataclass
class DependencyGraph:
    nodes: List[GraphNode] = field(default_factory=list)
    # package_name -> set of project names
    shared_packages: Dict[str, Set[str]] = field(default_factory=dict)


def build_graph(
    project_statuses: Dict[str, List[DependencyStatus]],
) -> DependencyGraph:
    """Build a dependency graph from a mapping of project -> statuses."""
    shared: Dict[str, Set[str]] = {}
    for project, statuses in project_statuses.items():
        for s in statuses:
            shared.setdefault(s.package, set()).add(project)

    nodes: List[GraphNode] = []
    for project, statuses in project_statuses.items():
        for s in statuses:
            dependents = sorted(shared[s.package] - {project})
            nodes.append(
                GraphNode(
                    project=project,
                    package=s.package,
                    current_version=s.current_version,
                    latest_version=s.latest_version,
                    is_outdated=s.is_outdated,
                    dependents=dependents,
                )
            )

    return DependencyGraph(nodes=nodes, shared_packages={k: v for k, v in shared.items()})


def shared_outdated(graph: DependencyGraph) -> Dict[str, List[str]]:
    """Return packages that are outdated in more than one project.

    Returns a dict of package_name -> sorted list of affected projects.
    """
    result: Dict[str, List[str]] = {}
    for package, projects in graph.shared_packages.items():
        outdated_in = sorted(
            p
            for node in graph.nodes
            if node.package == package and node.is_outdated
            for p in [node.project]
        )
        if len(set(outdated_in)) > 1:
            result[package] = sorted(set(outdated_in))
    return result


def format_graph_report(graph: DependencyGraph) -> str:
    """Render a human-readable summary of the dependency graph."""
    lines: List[str] = ["Dependency Graph Report", "=" * 40]
    shared = shared_outdated(graph)
    if shared:
        lines.append("Packages outdated across multiple projects:")
        for pkg, projects in sorted(shared.items()):
            lines.append(f"  {pkg}: {', '.join(projects)}")
    else:
        lines.append("No packages are outdated across multiple projects.")

    lines.append("")
    lines.append(f"Total nodes: {len(graph.nodes)}")
    total_shared = sum(1 for v in graph.shared_packages.values() if len(v) > 1)
    lines.append(f"Shared packages (2+ projects): {total_shared}")
    return "\n".join(lines)
