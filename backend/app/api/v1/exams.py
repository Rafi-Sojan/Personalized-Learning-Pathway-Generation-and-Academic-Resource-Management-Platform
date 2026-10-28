from collections import defaultdict

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import require_roles
from app.db.session import get_db
from app.models import Concept, Course, HistoricalExamQuestion, User
from app.schemas.learning import HistoricalExamImportRequest, HistoricalExamQuestionCreate, HistoricalExamQuestionResponse, HistoricalExamRanking
from app.services.audit import record_event
from ml.concept_mapping.topic_classifier import classify
from ml.preprocessing.question_parser import parse_questions

router = APIRouter()


def _course_for_user(course_id: str, user: User, db: Session) -> Course:
    course = db.scalar(select(Course).where(Course.id == course_id, Course.owner_id == user.id))
    if course is None and user.role in {"admin", "instructor"}:
        course = db.get(Course, course_id)
    if course is None:
        raise HTTPException(status_code=404, detail="Course not found")
    return course


def _concept_for_prompt(prompt: str, course_id: str, db: Session) -> tuple[str | None, str]:
    prediction = classify(prompt)
    concepts = db.scalars(select(Concept).where(Concept.course_id == course_id)).all()
    lowered = prompt.lower()
    match = next((concept for concept in concepts if concept.name.lower() in lowered), None)
    return (match.id if match else None, prediction.label)


@router.post("/questions", response_model=HistoricalExamQuestionResponse, status_code=201)
def create_question(payload: HistoricalExamQuestionCreate, current_user: User = Depends(require_roles("admin", "instructor")), db: Session = Depends(get_db)) -> HistoricalExamQuestionResponse:
    _course_for_user(payload.course_id, current_user, db)
    concept_id = payload.concept_id
    if concept_id and db.scalar(select(Concept).where(Concept.id == concept_id, Concept.course_id == payload.course_id)) is None:
        raise HTTPException(status_code=404, detail="Concept not found")
    concept_id, topic_label = (concept_id, "manual") if concept_id else _concept_for_prompt(payload.prompt, payload.course_id, db)
    question = HistoricalExamQuestion(course_id=payload.course_id, source=payload.source, exam_year=payload.exam_year, prompt=payload.prompt.strip(), concept_id=concept_id, topic_label=topic_label, difficulty=payload.difficulty)
    db.add(question)
    record_event(db, "historical_exam_question_created", current_user.id, metadata={"course_id": payload.course_id, "year": payload.exam_year})
    db.commit()
    db.refresh(question)
    return HistoricalExamQuestionResponse.model_validate(question)


@router.post("/import", response_model=list[HistoricalExamQuestionResponse], status_code=201)
def import_questions(payload: HistoricalExamImportRequest, current_user: User = Depends(require_roles("admin", "instructor")), db: Session = Depends(get_db)) -> list[HistoricalExamQuestionResponse]:
    _course_for_user(payload.course_id, current_user, db)
    questions = []
    for prompt in parse_questions(payload.text):
        concept_id, topic_label = _concept_for_prompt(prompt, payload.course_id, db)
        questions.append(HistoricalExamQuestion(course_id=payload.course_id, source=payload.source, exam_year=payload.exam_year, prompt=prompt, concept_id=concept_id, topic_label=topic_label, difficulty=1))
    if not questions:
        raise HTTPException(status_code=422, detail="No questions could be extracted")
    db.add_all(questions)
    record_event(db, "historical_exam_imported", current_user.id, metadata={"course_id": payload.course_id, "year": payload.exam_year, "question_count": len(questions)})
    db.commit()
    return [HistoricalExamQuestionResponse.model_validate(question) for question in questions]


@router.get("/questions", response_model=list[HistoricalExamQuestionResponse])
def list_questions(course_id: str, current_user: User = Depends(require_roles("admin", "instructor", "student")), db: Session = Depends(get_db)) -> list[HistoricalExamQuestionResponse]:
    _course_for_user(course_id, current_user, db)
    questions = db.scalars(select(HistoricalExamQuestion).where(HistoricalExamQuestion.course_id == course_id).order_by(HistoricalExamQuestion.exam_year.desc(), HistoricalExamQuestion.id)).all()
    return [HistoricalExamQuestionResponse.model_validate(question) for question in questions]


@router.get("/rankings", response_model=list[HistoricalExamRanking])
def historical_rankings(course_id: str, current_user: User = Depends(require_roles("admin", "instructor", "student")), db: Session = Depends(get_db)) -> list[HistoricalExamRanking]:
    _course_for_user(course_id, current_user, db)
    concepts = {concept.id: concept for concept in db.scalars(select(Concept).where(Concept.course_id == course_id)).all()}
    grouped: dict[str, list[int]] = defaultdict(list)
    for question in db.scalars(select(HistoricalExamQuestion).where(HistoricalExamQuestion.course_id == course_id, HistoricalExamQuestion.concept_id.is_not(None))).all():
        if question.concept_id:
            grouped[question.concept_id].append(question.difficulty)
    ranked = []
    for concept_id, difficulties in grouped.items():
        if concept_id not in concepts:
            continue
        average = sum(difficulties) / len(difficulties)
        ranked.append(HistoricalExamRanking(concept_id=concept_id, concept_name=concepts[concept_id].name, question_count=len(difficulties), average_difficulty=round(average, 2), score=round(len(difficulties) * average, 2)))
    return sorted(ranked, key=lambda item: (-item.score, item.concept_name))
