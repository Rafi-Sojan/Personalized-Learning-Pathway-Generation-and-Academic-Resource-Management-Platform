def prioritize(concepts: list[dict]) -> list[dict]:
    """Sort concepts with unfinished, higher-difficulty work before completed work."""
    return sorted(concepts, key=lambda item: (item.get("status") == "completed", -item.get("difficulty", 1)))
