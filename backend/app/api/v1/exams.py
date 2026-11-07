from collections import Counter, defaultdict
import hashlib
import logging
import uuid
from urllib.parse import quote
from io import BytesIO
from pathlib import Path
import tempfile

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, Response, UploadFile
from pypdf import PdfReader
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import get_current_user, require_roles
from app.db.session import get_db
from app.models import Concept, Course, HistoricalExamQuestion, Resource, SyllabusRecord, User
from app.schemas.learning import HistoricalExamImportRequest, HistoricalExamQuestionCreate, HistoricalExamQuestionResponse, HistoricalExamRanking
from app.services.audit import record_event
from app.services.storage import storage
from ml.concept_mapping.semantic_matcher import topic_similarity
from ml.concept_mapping.text_cleaner import clean_text
from ml.preprocessing.ocr_processor import run_pdf_ocr
from ml.preprocessing.question_parser import parse_question_records
from app.services.syllabus_service import extract_declared_course_codes

router = APIRouter()
logger = logging.getLogger(__name__)


def _course_for_user(course_id: str, user: User, db: Session) -> Course:
    """Resolve a course the caller owns, allowing instructors and admins broader access."""
    course = db.scalar(select(Course).where(Course.id == course_id, Course.owner_id == user.id))
    if course is None and user.role in {"admin", "instructor"}:
        course = db.get(Course, course_id)
    if course is None:
        raise HTTPException(status_code=404, detail="Course not found")
    return course


def _assert_document_course(text: str, course: Course) -> None:
    """Reject a paper whose explicit RVCE course code disagrees with the selected subject."""
    declared = extract_declared_course_codes(text)
    selected = "".join(character for character in course.code.upper() if character.isalnum())
    if declared and selected not in declared:
        printed = ", ".join(sorted(declared))
        raise HTTPException(status_code=422, detail=f"This paper declares course code {printed}, not {course.code}")


def _verified_syllabus_concepts(course_id: str, db: Session) -> list[Concept]:
    """Return current concepts backed by a human-verified syllabus record."""
    return list(db.scalars(
        select(Concept)
        .join(SyllabusRecord, SyllabusRecord.mapped_concept_id == Concept.id)
        .where(
            Concept.course_id == course_id,
            Concept.syllabus_version_id.is_not(None),
            SyllabusRecord.syllabus_version_id == Concept.syllabus_version_id,
            SyllabusRecord.review_status == "verified",
        )
        .distinct()
    ).all())


def _concept_for_prompt(prompt: str, course_id: str, db: Session) -> tuple[str | None, str, float | None]:
    """Suggest an unambiguous mapping only among reviewed concepts in the same course."""
    ranked = sorted(
        ((topic_similarity(prompt, concept.name), concept) for concept in _verified_syllabus_concepts(course_id, db)),
        key=lambda pair: pair[0],
        reverse=True,
    )
    if not ranked:
        return None, "Unmapped", None
    best_score, best = ranked[0]
    runner_up = ranked[1][0] if len(ranked) > 1 else 0.0
    if best_score < 0.62 or (best_score < 0.9 and best_score - runner_up < 0.08):
        return None, "Unmapped", None
    return best.id, best.name, best_score


@router.post("/questions", response_model=HistoricalExamQuestionResponse, status_code=201)
def create_question(payload: HistoricalExamQuestionCreate, current_user: User = Depends(require_roles("admin", "instructor")), db: Session = Depends(get_db)) -> HistoricalExamQuestionResponse:
    """Persist one authorized historical question with an explicit or inferred concept link."""
    _course_for_user(payload.course_id, current_user, db)
    concept_id = payload.concept_id
    if concept_id and db.scalar(select(Concept).where(Concept.id == concept_id, Concept.course_id == payload.course_id)) is None:
        raise HTTPException(status_code=404, detail="Concept not found")
    concept_id, topic_label, confidence = (concept_id, "manual", 1.0) if concept_id else _concept_for_prompt(payload.prompt, payload.course_id, db)
    question = HistoricalExamQuestion(course_id=payload.course_id, source=payload.source, source_document=payload.source, exam_year=payload.exam_year, prompt=payload.prompt.strip(), concept_id=concept_id, topic_label=topic_label, difficulty=payload.difficulty, paper_part=payload.paper_part, question_kind=payload.question_kind, assessment_type=payload.assessment_type, question_format=payload.question_format, marks=payload.marks, mapping_confidence=confidence, review_status="pending_review")
    db.add(question)
    record_event(db, "historical_exam_question_created", current_user.id, metadata={"course_id": payload.course_id, "year": payload.exam_year})
    db.commit()
    db.refresh(question)
    return HistoricalExamQuestionResponse.model_validate(question)


@router.post("/import", response_model=list[HistoricalExamQuestionResponse], status_code=201)
def import_questions(payload: HistoricalExamImportRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> list[HistoricalExamQuestionResponse]:
    """Parse an owned paper's text and save prompts with best-effort concept associations."""
    course = _course_for_user(payload.course_id, current_user, db)
    _assert_document_course(payload.text, course)
    return _persist_parsed_questions(payload.course_id, payload.source, payload.exam_year, payload.text, current_user, db, assessment_type=payload.assessment_type, question_format=payload.question_format, part_a_is_quiz=payload.part_a_is_quiz, source_document=payload.source)


@router.post("/import-pdf", response_model=list[HistoricalExamQuestionResponse], status_code=201)
async def import_question_paper_pdf(
    course_id: str = Query(...),
    source: str = Form(min_length=1, max_length=240),
    exam_year: int = Form(ge=1900, le=2100),
    assessment_type: str = Form(pattern="^(quiz|test|see|assignment|lab|practice|unknown)$"),
    question_format: str = Form(default="unknown", pattern="^(objective|short|long|numerical|coding|practical|unknown)$"),
    part_a_is_quiz: bool = Form(default=False),
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[HistoricalExamQuestionResponse]:
    """Extract numbered prompts from an uploaded PDF for a course the caller owns."""
    course = _course_for_user(course_id, current_user, db)
    if file.content_type != "application/pdf" or not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=415, detail="Only PDF question papers are supported")
    data = await file.read(settings.max_upload_bytes + 1)
    if len(data) > settings.max_upload_bytes:
        raise HTTPException(status_code=413, detail="Question paper exceeds the configured upload limit")
    if not data.startswith(b"%PDF-"):
        raise HTTPException(status_code=415, detail="Uploaded content is not a valid PDF")
    try:
        reader = PdfReader(BytesIO(data), strict=False)
        if reader.is_encrypted:
            raise HTTPException(status_code=422, detail="Encrypted question papers are not supported")
        if len(reader.pages) > settings.max_pdf_pages:
            raise HTTPException(status_code=413, detail="Question paper exceeds the configured page limit")
        text = "\n".join(f"[[PAGE {index}]]\n{page.extract_text() or ''}" for index, page in enumerate(reader.pages, start=1))[: settings.max_extracted_text_chars]
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=422, detail="The uploaded PDF could not be read") from exc
    if len(text.strip()) < 20 and settings.ocr_enabled:
        with tempfile.TemporaryDirectory() as directory:
            pdf_path = Path(directory) / "question-paper.pdf"
            pdf_path.write_bytes(data)
            try:
                text = run_pdf_ocr(str(pdf_path), settings.max_extracted_text_chars)
            except RuntimeError as exc:
                raise HTTPException(status_code=503, detail=str(exc)) from exc
    if len(text.strip()) < 20:
        raise HTTPException(status_code=422, detail="No readable text found; enable OCR for scanned question papers")
    _assert_document_course(text, course)
    source_filename = Path(file.filename or source).name[:500]
    storage_key = f"exam-{uuid.uuid4()}.pdf"
    checksum = hashlib.sha256(data).hexdigest()
    duplicate_resource = db.scalar(select(Resource).where(
        Resource.course_id == course_id,
        Resource.kind == "historical_exam_pdf",
        Resource.checksum == checksum,
    ))
    if duplicate_resource is not None:
        raise HTTPException(status_code=409, detail="This question-paper PDF has already been imported for the subject")
    try:
        storage.put_bytes(storage_key, data, content_type="application/pdf")
        source_resource = Resource(course_id=course_id, title=source_filename[:240], kind="historical_exam_pdf", storage_key=storage_key, checksum=checksum, processing_status="ready")
        db.add(source_resource)
        db.flush()
        return _persist_parsed_questions(course_id, source, exam_year, text, current_user, db, assessment_type=assessment_type, question_format=question_format, part_a_is_quiz=part_a_is_quiz, source_document=source_filename, source_resource_id=source_resource.id)
    except Exception:
        db.rollback()
        try:
            storage.delete(storage_key)
        except Exception:
            logger.exception("Failed to remove an uncommitted historical-paper object: %s", storage_key)
        raise


def _persist_parsed_questions(course_id: str, source: str, exam_year: int, text: str, user: User, db: Session, *, assessment_type: str = "unknown", question_format: str = "unknown", part_a_is_quiz: bool = True, source_document: str = "", source_resource_id: str | None = None) -> list[HistoricalExamQuestionResponse]:
    """Parse paper text, skip exact duplicate imports, and persist new question rows."""
    parsed_questions = parse_question_records(text, part_a_is_quiz=part_a_is_quiz)
    if not parsed_questions:
        raise HTTPException(status_code=422, detail="No questions could be extracted")
    questions = []
    for parsed in parsed_questions:
        prompt = parsed.prompt
        duplicate = db.scalar(select(HistoricalExamQuestion).where(
            HistoricalExamQuestion.course_id == course_id,
            HistoricalExamQuestion.source == source,
            HistoricalExamQuestion.exam_year == exam_year,
            HistoricalExamQuestion.source_document == source_document,
            HistoricalExamQuestion.prompt == prompt,
            HistoricalExamQuestion.paper_part == parsed.paper_part,
            HistoricalExamQuestion.question_kind == parsed.question_kind,
            HistoricalExamQuestion.source_page == parsed.source_page,
            HistoricalExamQuestion.question_number == parsed.question_number,
            HistoricalExamQuestion.subpart == parsed.subpart,
        ))
        if duplicate:
            continue
        concept_id, topic_label, confidence = _concept_for_prompt(prompt, course_id, db)
        question_kind = parsed.question_kind
        detected_assessment = parsed.assessment_type or assessment_type
        detected_format = parsed.question_format if parsed.question_format != "unknown" else question_format
        questions.append(HistoricalExamQuestion(course_id=course_id, source=source, source_document=source_document, source_resource_id=source_resource_id, exam_year=exam_year, prompt=prompt, concept_id=concept_id, topic_label=topic_label, difficulty=None, paper_part=parsed.paper_part, question_kind=question_kind, question_number=parsed.question_number, subpart=parsed.subpart, marks=parsed.marks, source_page=parsed.source_page, assessment_type=detected_assessment, question_format=detected_format, mapping_confidence=confidence, review_status="pending_review"))
    if not questions:
        raise HTTPException(status_code=409, detail="This paper has already been imported")
    db.add_all(questions)
    record_event(db, "historical_exam_imported", user.id, metadata={"course_id": course_id, "year": exam_year, "question_count": len(questions)})
    db.flush()
    responses = [HistoricalExamQuestionResponse.model_validate(question) for question in questions]
    db.commit()
    return responses


@router.get("/questions", response_model=list[HistoricalExamQuestionResponse])
def list_questions(
    course_id: str,
    year_from: int | None = Query(default=None, ge=1900, le=2100),
    year_to: int | None = Query(default=None, ge=1900, le=2100),
    search: str | None = Query(default=None, max_length=200),
    assessment_type: str | None = Query(default=None, pattern="^(quiz|test|see|assignment|lab|practice|unknown)$"),
    question_format: str | None = Query(default=None, pattern="^(objective|short|long|numerical|coding|practical|unknown)$"),
    topic: str | None = Query(default=None, max_length=120),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[HistoricalExamQuestionResponse]:
    """List question records for a course the caller is authorized to access."""
    _course_for_user(course_id, current_user, db)
    if year_from is not None and year_to is not None and year_from > year_to:
        raise HTTPException(status_code=422, detail="The start year must not exceed the end year")
    query = select(HistoricalExamQuestion).where(HistoricalExamQuestion.course_id == course_id)
    if year_from is not None:
        query = query.where(HistoricalExamQuestion.exam_year >= year_from)
    if year_to is not None:
        query = query.where(HistoricalExamQuestion.exam_year <= year_to)
    if search:
        query = query.where(HistoricalExamQuestion.prompt.ilike(f"%{search.strip()}%"))
    if assessment_type:
        query = query.where(HistoricalExamQuestion.assessment_type == assessment_type)
    if question_format:
        query = query.where(HistoricalExamQuestion.question_format == question_format)
    if topic:
        query = query.where(HistoricalExamQuestion.topic_label.ilike(f"%{topic.strip()}%"))
    questions = db.scalars(query.order_by(HistoricalExamQuestion.exam_year.desc(), HistoricalExamQuestion.id)).all()
    return [HistoricalExamQuestionResponse.model_validate(question) for question in questions]


@router.get("/rankings", response_model=list[HistoricalExamRanking])
def historical_rankings(course_id: str, current_user: User = Depends(require_roles("admin", "instructor", "student")), db: Session = Depends(get_db)) -> list[HistoricalExamRanking]:
    """Rank concepts by stored historical-question frequency and difficulty evidence."""
    _course_for_user(course_id, current_user, db)
    concepts = {concept.id: concept for concept in _verified_syllabus_concepts(course_id, db)}
    grouped: dict[str, list[HistoricalExamQuestion]] = defaultdict(list)
    for question in db.scalars(select(HistoricalExamQuestion).where(HistoricalExamQuestion.course_id == course_id, HistoricalExamQuestion.concept_id.is_not(None), HistoricalExamQuestion.question_kind == "main", HistoricalExamQuestion.review_status == "verified")).all():
        if question.concept_id:
            grouped[question.concept_id].append(question)
    ranked = []
    for concept_id, questions in grouped.items():
        if concept_id not in concepts:
            continue
        known_difficulties = [question.difficulty for question in questions if question.difficulty is not None]
        average = round(sum(known_difficulties) / len(known_difficulties), 2) if known_difficulties else None
        score = len(questions) * (average if average is not None else 1)
        ranked.append(HistoricalExamRanking(concept_id=concept_id, concept_name=concepts[concept_id].name, question_count=len(questions), average_difficulty=average, score=round(score, 2)))
    return sorted(ranked, key=lambda item: (-item.score, item.concept_name))


@router.get("/frequency")
def historical_frequency(
    course_id: str,
    year_from: int | None = Query(default=None, ge=1900, le=2100),
    year_to: int | None = Query(default=None, ge=1900, le=2100),
    assessment_type: str | None = Query(default=None, pattern="^(quiz|test|see|assignment|lab|practice|unknown)$"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    """Summarize question counts by mapped topic and examination year for one subject."""
    _course_for_user(course_id, current_user, db)
    if year_from is not None and year_to is not None and year_from > year_to:
        raise HTTPException(status_code=422, detail="The start year must not exceed the end year")
    query = select(HistoricalExamQuestion).where(HistoricalExamQuestion.course_id == course_id, HistoricalExamQuestion.review_status == "verified")
    if year_from is not None:
        query = query.where(HistoricalExamQuestion.exam_year >= year_from)
    if year_to is not None:
        query = query.where(HistoricalExamQuestion.exam_year <= year_to)
    if assessment_type:
        query = query.where(HistoricalExamQuestion.assessment_type == assessment_type)
    questions = db.scalars(query).all()
    quiz_count = sum(question.question_kind == "quiz" for question in questions)
    main_questions = [question for question in questions if question.question_kind == "main"]
    concepts = {item.id: item.name for item in _verified_syllabus_concepts(course_id, db)}
    mapped_main_questions = [question for question in main_questions if question.concept_id in concepts]
    unmapped_main_count = len(main_questions) - len(mapped_main_questions)
    grouped: dict[str, dict] = {}
    prompt_counts: Counter[tuple[str, str]] = Counter()
    for question in mapped_main_questions:
        topic_key = question.concept_id or ""
        topic_name = concepts[topic_key]
        record = grouped.setdefault(topic_key, {"topic_key": topic_key, "topic_name": topic_name, "question_count": 0, "year_counts": defaultdict(int), "last_seen": question.exam_year, "total_marks": 0.0, "supporting_questions": []})
        record["question_count"] += 1
        record["year_counts"][question.exam_year] += 1
        record["last_seen"] = max(record["last_seen"], question.exam_year)
        record["total_marks"] += question.marks or 0.0
        record["supporting_questions"].append({"id": question.id, "year": question.exam_year, "source": question.source, "source_document": question.source_document, "source_page": question.source_page, "marks": question.marks})
        prompt_counts[(topic_key, clean_text(question.prompt))] += 1
    topics = []
    for record in grouped.values():
        record["repeat_count"] = sum(count - 1 for (key, _), count in prompt_counts.items() if key == record["topic_key"] and count > 1)
        record["total_marks"] = round(record["total_marks"], 2)
        record["year_counts"] = [{"year": year, "count": count} for year, count in sorted(record["year_counts"].items())]
        topics.append(record)
    topics.sort(key=lambda item: (-item["question_count"], item["topic_name"].casefold()))
    # Include evidence identifiers so displayed counts can be traced to reviewed source questions.
    return {"course_id": course_id, "question_count": len(questions), "main_question_count": len(main_questions), "mapped_main_question_count": len(mapped_main_questions), "unmapped_main_question_count": unmapped_main_count, "quiz_count": quiz_count, "year_from": year_from, "year_to": year_to, "topics": topics}


@router.post("/questions/{question_id}/review")
def review_question(
    question_id: str,
    status: str = Query(..., pattern="^(verified|rejected|pending_review)$"),
    difficulty: int | None = Query(default=None, ge=1, le=5),
    assessment_type: str | None = Query(default=None, pattern="^(quiz|test|see|assignment|lab|practice|unknown)$"),
    question_format: str | None = Query(default=None, pattern="^(objective|short|long|numerical|coding|practical|unknown)$"),
    concept_id: str | None = Query(default=None),
    clear_concept: bool = Query(default=False),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    """Let the course owner verify or reject an imported historical question record."""
    question = db.scalar(select(HistoricalExamQuestion).join(Course, Course.id == HistoricalExamQuestion.course_id).where(HistoricalExamQuestion.id == question_id, Course.owner_id == current_user.id))
    if question is None and current_user.role in {"admin", "instructor"}:
        question = db.get(HistoricalExamQuestion, question_id)
    if question is None:
        raise HTTPException(status_code=404, detail="Question record not found")
    question.review_status = status
    if difficulty is not None:
        question.difficulty = difficulty
    if assessment_type is not None:
        question.assessment_type = assessment_type
    if question_format is not None:
        question.question_format = question_format
    if clear_concept:
        question.concept_id = None
        question.topic_label = "Unmapped"
        question.mapping_confidence = None
    elif concept_id is not None:
        concept = next((item for item in _verified_syllabus_concepts(question.course_id, db) if item.id == concept_id), None)
        if concept is None:
            raise HTTPException(status_code=404, detail="Verified syllabus concept not found for this subject")
        question.concept_id = concept.id
        question.topic_label = concept.name
        question.mapping_confidence = 1.0
    db.commit()
    return {"id": question.id, "review_status": question.review_status, "difficulty": question.difficulty, "assessment_type": question.assessment_type, "question_format": question.question_format, "concept_id": question.concept_id, "topic_label": question.topic_label}


@router.get("/papers/{resource_id}")
def get_source_paper(resource_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> Response:
    """Serve the retained source PDF for an owned imported paper with page context."""
    resource = db.scalar(select(Resource).join(Course, Course.id == Resource.course_id).where(
        Resource.id == resource_id,
        Resource.kind == "historical_exam_pdf",
        Course.owner_id == current_user.id,
    ))
    if resource is None and current_user.role in {"admin", "instructor"}:
        resource = db.scalar(select(Resource).where(Resource.id == resource_id, Resource.kind == "historical_exam_pdf"))
    if resource is None or not resource.storage_key:
        raise HTTPException(status_code=404, detail="Source paper not found")
    filename = quote(Path(resource.title).name or "question-paper.pdf")
    return Response(
        content=storage.read_bytes(resource.storage_key),
        media_type="application/pdf",
        headers={"Content-Disposition": f"inline; filename*=UTF-8''{filename}", "X-Content-Type-Options": "nosniff"},
    )
