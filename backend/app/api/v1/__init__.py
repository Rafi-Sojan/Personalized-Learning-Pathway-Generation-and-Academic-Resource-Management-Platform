from fastapi import APIRouter

from app.api.v1 import admin, auth, concepts, courses, exams, progress, quizzes, rankings, resources, roadmap, syllabus

router = APIRouter()
router.include_router(auth.router, prefix="/auth", tags=["auth"])
router.include_router(admin.router, prefix="/admin", tags=["admin"])
router.include_router(exams.router, prefix="/exams", tags=["exams"])
router.include_router(courses.router, prefix="/courses", tags=["courses"])
router.include_router(syllabus.router, prefix="/syllabus", tags=["syllabus"])
router.include_router(concepts.router, prefix="/concepts", tags=["concepts"])
router.include_router(resources.router, prefix="/resources", tags=["resources"])
router.include_router(roadmap.router, prefix="/roadmap", tags=["roadmap"])
router.include_router(roadmap.router, prefix="/roadmaps", tags=["roadmaps"])
router.include_router(quizzes.router, prefix="/quizzes", tags=["quizzes"])
router.include_router(progress.router, prefix="/progress", tags=["progress"])
router.include_router(rankings.router, prefix="/rankings", tags=["rankings"])
