"""Deterministic validation and ordering for prerequisite graphs."""

from __future__ import annotations

from collections import defaultdict
import heapq


def topological_order(edges: dict[str, list[str]]) -> list[str]:
    """Return stable prerequisite-first order or reject malformed cyclic edges."""
    incoming: dict[str, int] = defaultdict(int)
    dependents: dict[str, set[str]] = defaultdict(set)
    for node, prerequisites in edges.items():
        incoming.setdefault(node, 0)
        for prerequisite in set(prerequisites):
            if prerequisite == node:
                raise ValueError(f"dependency graph contains a self-cycle at {node}")
            incoming.setdefault(prerequisite, 0)
            incoming[node] += 1
            dependents[prerequisite].add(node)
    queue = [node for node, count in incoming.items() if count == 0]
    heapq.heapify(queue)
    ordered: list[str] = []
    while queue:
        node = heapq.heappop(queue)
        ordered.append(node)
        for child in sorted(dependents[node]):
            incoming[child] -= 1
            if incoming[child] == 0:
                heapq.heappush(queue, child)
    if len(ordered) != len(incoming):
        blocked = ", ".join(sorted(node for node, count in incoming.items() if count > 0))
        raise ValueError(f"dependency graph contains a cycle involving: {blocked}")
    return ordered
