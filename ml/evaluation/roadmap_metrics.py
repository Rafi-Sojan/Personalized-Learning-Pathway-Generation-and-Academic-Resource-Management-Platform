def completion_rate(completed: int, planned: int) -> float:
    return completed / planned if planned else 0.0
