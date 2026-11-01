from app.services.syllabus_service import extract_topics


def map_syllabus(text: str) -> dict:
    """Run the local topic classifier and syllabus crosswalk for the submitted text."""
    topics = extract_topics(text)
    return {"topics": topics, "count": len(topics), "status": "completed"}
