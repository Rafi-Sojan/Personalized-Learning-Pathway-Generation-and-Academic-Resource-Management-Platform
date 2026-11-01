from datetime import date, timedelta

from .time_estimator import estimate_minutes


def schedule(concepts: list[dict], start: date | None = None) -> list[dict]:
    """Assign each concept a consecutive study date and estimated duration."""
    start = start or date.today()
    return [{"concept_id": item["id"], "date": start + timedelta(days=index), "minutes": estimate_minutes(item.get("difficulty", 1))} for index, item in enumerate(concepts)]
