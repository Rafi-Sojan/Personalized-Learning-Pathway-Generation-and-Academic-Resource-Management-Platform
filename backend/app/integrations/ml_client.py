from app.services.syllabus_service import extract_topics


def map_syllabus(text: str) -> dict:
    topics = extract_topics(text)
    return {"topics": topics, "count": len(topics), "status": "completed"}
