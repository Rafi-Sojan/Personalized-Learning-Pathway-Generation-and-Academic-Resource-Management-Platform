def completion_rate(completed: int, planned: int) -> float:
    """Return the completed-to-planned ratio, with zero for an empty plan."""
    return completed / planned if planned else 0.0
