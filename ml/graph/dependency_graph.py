from collections import defaultdict, deque


def topological_order(edges: dict[str, list[str]]) -> list[str]:
    incoming = defaultdict(int)
    for node, prerequisites in edges.items():
        incoming.setdefault(node, 0)
        for prerequisite in prerequisites:
            incoming[node] += 1
            incoming.setdefault(prerequisite, 0)
    queue = deque(node for node, count in incoming.items() if count == 0)
    ordered = []
    while queue:
        node = queue.popleft()
        ordered.append(node)
        for child, prerequisites in edges.items():
            if node in prerequisites:
                incoming[child] -= 1
                if incoming[child] == 0:
                    queue.append(child)
    if len(ordered) != len(incoming):
        raise ValueError("dependency graph contains a cycle")
    return ordered
