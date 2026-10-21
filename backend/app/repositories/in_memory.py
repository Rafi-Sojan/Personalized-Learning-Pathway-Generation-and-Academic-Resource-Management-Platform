from copy import deepcopy


class InMemoryRepository:
    def __init__(self) -> None:
        self.courses = [
            {"id": "course-python", "code": "CS101", "title": "Python Foundations", "description": "Core programming and problem solving.", "progress": 42, "concept_count": 8},
            {"id": "course-data", "code": "DS201", "title": "Data Structures", "description": "Algorithms, complexity, and practical structures.", "progress": 18, "concept_count": 6},
        ]
        self.concepts = [
            {"id": "variables", "name": "Variables and Types", "course_id": "course-python", "difficulty": 1, "status": "completed", "prerequisites": []},
            {"id": "control-flow", "name": "Control Flow", "course_id": "course-python", "difficulty": 2, "status": "in_progress", "prerequisites": ["variables"]},
            {"id": "functions", "name": "Functions", "course_id": "course-python", "difficulty": 2, "status": "not_started", "prerequisites": ["control-flow"]},
            {"id": "complexity", "name": "Complexity Analysis", "course_id": "course-data", "difficulty": 3, "status": "not_started", "prerequisites": []},
        ]
        self.resources = [
            {"id": "res-1", "title": "Python control flow guide", "kind": "article", "url": "https://docs.python.org/3/tutorial/controlflow.html", "concept_id": "control-flow", "duration_minutes": 25},
            {"id": "res-2", "title": "Functions in Python", "kind": "video", "url": "https://www.youtube.com/results?search_query=python+functions", "concept_id": "functions", "duration_minutes": 35},
        ]
        self.progress: dict[str, dict] = {}

    def clone(self, value):
        return deepcopy(value)


repository = InMemoryRepository()
