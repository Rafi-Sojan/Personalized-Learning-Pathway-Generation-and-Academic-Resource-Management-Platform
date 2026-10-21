def prioritize(concepts: list[dict]) -> list[dict]:
    return sorted(concepts, key=lambda item: (item.get("status") == "completed", -item.get("difficulty", 1)))
