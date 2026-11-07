"""Legacy in-memory roadmap utility retained for compatibility."""

from datetime import date, timedelta
from typing import cast

from app.repositories.in_memory import repository


def build_roadmap(days: int = 14) -> list[dict]:
    """Build a deterministic sample schedule from legacy utility fixtures."""
    pending = [concept for concept in repository.concepts if concept["status"] != "completed"]
    return [
        {
            "id": f"plan-{concept['id']}",
            "concept_id": concept["id"],
            "concept_name": concept["name"],
            "scheduled_date": date.today() + timedelta(days=min(index, max(days - 1, 0))),
            "minutes": 25 + cast(int, concept["difficulty"]) * 10,
            "status": "planned",
            "reason": "Prerequisites are available and this topic is not complete.",
        }
        for index, concept in enumerate(pending)
    ]
