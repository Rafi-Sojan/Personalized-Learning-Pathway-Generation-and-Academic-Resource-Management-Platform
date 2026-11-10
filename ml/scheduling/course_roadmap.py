"""Course-type-aware activity construction and balanced calendar scheduling."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, replace
from datetime import date, timedelta
import math
from typing import Mapping, Sequence


ROADMAP_SESSION_ALGORITHM_VERSION = "rvce-activity-roadmap-v3"
ROADMAP_MODES = frozenset({"full_term", "cie", "see", "revision"})
MODE_FACTORS = {"full_term": 1.0, "cie": 0.55, "see": 0.45, "revision": 0.30}


@dataclass(frozen=True)
class ActivityDemand:
    """Describe one ordered learning activity before calendar capacity is applied."""

    demand_id: str
    course_id: str
    course_code: str
    course_title: str
    concept_id: str
    concept_name: str
    syllabus_version_id: str | None
    unit_label: str | None
    source_page: int | None
    assessment_scope: str
    activity_type: str
    modality: str
    minutes: int
    reason: str
    evidence_question_ids: tuple[str, ...] = ()


@dataclass(frozen=True)
class ScheduledActivity:
    """Represent one capacity-bounded calendar segment of an activity demand."""

    demand_id: str
    course_id: str
    course_code: str
    course_title: str
    concept_id: str
    concept_name: str
    syllabus_version_id: str | None
    unit_label: str | None
    source_page: int | None
    assessment_scope: str
    activity_type: str
    modality: str
    scheduled_date: date
    minutes: int
    reason: str
    evidence_question_ids: tuple[str, ...] = ()


@dataclass
class _PendingDemand:
    """Track unscheduled minutes without mutating the immutable source demand."""

    demand: ActivityDemand
    remaining: int


_MIXES: dict[str, tuple[tuple[str, str, float], ...]] = {
    "generic": (("learn", "self_study", 1.0),),
    "theory": (
        ("learn", "lecture", 0.45),
        ("application", "experiential", 0.25),
        ("retrieval", "self_study", 0.20),
        ("review", "self_study", 0.10),
    ),
    "numerical_theory": (
        ("learn", "lecture", 0.25),
        ("worked_example", "tutorial", 0.20),
        ("problem_practice", "tutorial", 0.40),
        ("retrieval", "self_study", 0.15),
    ),
    "theory_lab": (
        ("learn", "lecture", 0.35),
        ("application", "experiential", 0.15),
        ("lab_practice", "practical", 0.35),
        ("lab_review", "self_study", 0.15),
    ),
    "programming": (
        ("learn", "lecture", 0.20),
        ("code_along", "practical", 0.25),
        ("coding_practice", "practical", 0.35),
        ("mini_project", "experiential", 0.15),
        ("retrieval", "self_study", 0.05),
    ),
    "project": (
        ("plan", "practical", 0.10),
        ("prototype", "practical", 0.45),
        ("test", "practical", 0.25),
        ("document", "experiential", 0.10),
        ("demonstrate", "practical", 0.10),
    ),
    "cad": (
        ("learn", "lecture", 0.15),
        ("guided_drawing", "practical", 0.25),
        ("cad_practice", "practical", 0.45),
        ("mock_drawing", "practical", 0.15),
    ),
    "language": (
        ("diagnostic", "practical", 0.10),
        ("listening", "practical", 0.18),
        ("speaking", "practical", 0.18),
        ("reading", "practical", 0.18),
        ("writing", "practical", 0.26),
        ("retrieval", "self_study", 0.10),
    ),
    "objective_hss": (
        ("learn", "lecture", 0.35),
        ("case_study", "experiential", 0.25),
        ("retrieval", "self_study", 0.25),
        ("mock_objective", "self_study", 0.15),
    ),
    "health_practice": (
        ("learn", "lecture", 0.15),
        ("guided_practice", "practical", 0.55),
        ("demonstration", "practical", 0.20),
        ("reflection", "experiential", 0.10),
    ),
}


def activity_mix(course_type: str, mode: str) -> tuple[tuple[str, str, float], ...]:
    """Return the deterministic activity mix for a reviewed course type and plan mode."""
    if mode not in ROADMAP_MODES:
        raise ValueError(f"unsupported roadmap mode: {mode}")
    if mode == "revision":
        if course_type in {"numerical_theory", "programming", "cad"}:
            return (("exam_practice", "self_study", 0.60), ("retrieval", "self_study", 0.25), ("review", "self_study", 0.15))
        if course_type in {"theory_lab", "project", "health_practice"}:
            return (("demonstration_review", "practical", 0.50), ("retrieval", "self_study", 0.25), ("review", "self_study", 0.25))
        return (("retrieval", "self_study", 0.45), ("exam_practice", "self_study", 0.40), ("review", "self_study", 0.15))
    return _MIXES.get(course_type, _MIXES["generic"])


def adjusted_minutes(base_minutes: int, mastery_score: float | None, mode: str) -> int:
    """Compress by plan mode and adapt effort to the learner's latest mastery evidence."""
    if mode not in MODE_FACTORS:
        raise ValueError(f"unsupported roadmap mode: {mode}")
    mastery_factor = 1.0
    if mastery_score is not None:
        bounded = max(0.0, min(100.0, mastery_score))
        if bounded >= 85:
            mastery_factor = 0.55
        elif bounded >= 70:
            mastery_factor = 0.72
        elif bounded >= 50:
            mastery_factor = 0.90
        elif bounded < 30:
            mastery_factor = 1.15
    return max(10, round(max(1, base_minutes) * MODE_FACTORS[mode] * mastery_factor))


def included_in_mode(assessment_scope: str, mode: str) -> bool:
    """Exclude explicitly CIE-only material from SEE plans while retaining full coverage elsewhere."""
    if mode == "see" and assessment_scope == "cie_only":
        return False
    if mode == "cie" and assessment_scope == "see_only":
        return False
    return True


def _split_minutes(total_minutes: int, mix: Sequence[tuple[str, str, float]]) -> list[tuple[str, str, int]]:
    """Allocate exact minutes across meaningful activities with a ten-minute minimum block."""
    total = max(1, total_minutes)
    active = [item for item in mix if item[2] > 0]
    while len(active) > 1 and len(active) * 10 > total:
        smallest = min(range(len(active)), key=lambda index: active[index][2])
        active.pop(smallest)
    if len(active) == 1:
        return [(active[0][0], active[0][1], total)]
    base = [10 for _ in active]
    remaining = total - sum(base)
    weight_total = sum(item[2] for item in active)
    raw_extras = [remaining * item[2] / weight_total for item in active]
    extras = [math.floor(value) for value in raw_extras]
    for index in sorted(range(len(active)), key=lambda item: raw_extras[item] - extras[item], reverse=True)[: remaining - sum(extras)]:
        extras[index] += 1
    return [(item[0], item[1], base[index] + extras[index]) for index, item in enumerate(active)]


def build_concept_demands(
    *,
    demand_prefix: str,
    course_id: str,
    course_code: str,
    course_title: str,
    course_type: str,
    concept_id: str,
    concept_name: str,
    syllabus_version_id: str | None,
    unit_label: str | None,
    source_page: int | None,
    assessment_scope: str,
    base_minutes: int,
    mastery_score: float | None,
    mode: str,
    reason: str,
    main_question_ids: Sequence[str] = (),
    quiz_question_ids: Sequence[str] = (),
) -> list[ActivityDemand]:
    """Expand one concept estimate into ordered course-type-specific learning activities."""
    if not included_in_mode(assessment_scope, mode):
        return []
    minutes = adjusted_minutes(base_minutes, mastery_score, mode)
    demands: list[ActivityDemand] = []
    for index, (activity_type, modality, activity_minutes) in enumerate(_split_minutes(minutes, activity_mix(course_type, mode))):
        evidence = quiz_question_ids if activity_type in {"retrieval", "mock_objective"} and quiz_question_ids else main_question_ids
        demands.append(ActivityDemand(
            demand_id=f"{demand_prefix}-{index}",
            course_id=course_id,
            course_code=course_code,
            course_title=course_title,
            concept_id=concept_id,
            concept_name=concept_name,
            syllabus_version_id=syllabus_version_id,
            unit_label=unit_label,
            source_page=source_page,
            assessment_scope=assessment_scope,
            activity_type=activity_type,
            modality=modality,
            minutes=activity_minutes,
            reason=reason,
            evidence_question_ids=tuple(dict.fromkeys(evidence)),
        ))
    return demands


def available_dates(start_date: date, target_date: date, unavailable_weekdays: Sequence[int] = ()) -> list[date]:
    """Return inclusive study dates after applying validated weekday exclusions."""
    if target_date < start_date:
        raise ValueError("target date must not precede start date")
    excluded = set(unavailable_weekdays)
    if any(day < 0 or day > 6 for day in excluded):
        raise ValueError("unavailable weekdays must use values 0 through 6")
    count = (target_date - start_date).days + 1
    return [start_date + timedelta(days=offset) for offset in range(count) if (start_date + timedelta(days=offset)).weekday() not in excluded]


def schedule_activity_demands(
    demands_by_course: Mapping[str, Sequence[ActivityDemand]],
    *,
    start_date: date,
    target_date: date,
    daily_minutes: int,
    unavailable_weekdays: Sequence[int] = (),
    allow_partial: bool = False,
    max_session_minutes: int = 60,
) -> list[ScheduledActivity]:
    """Interleave course queues without violating their internal order or daily capacity."""
    if daily_minutes <= 0:
        raise ValueError("daily minutes must be positive")
    dates = available_dates(start_date, target_date, unavailable_weekdays)
    if not dates:
        raise ValueError("no study dates remain after weekday exclusions")
    required = sum(item.minutes for values in demands_by_course.values() for item in values)
    capacity = len(dates) * daily_minutes
    if required > capacity and not allow_partial:
        raise ValueError("deadline is infeasible for the available daily study time")
    queues = {
        course_id: deque(_PendingDemand(item, item.minutes) for item in values)
        for course_id, values in sorted(demands_by_course.items())
        if values
    }
    rotation = list(queues)
    cursor = 0
    scheduled: list[ScheduledActivity] = []
    for study_date in dates:
        remaining_day = daily_minutes
        used_courses: set[str] = set()
        while remaining_day > 0 and any(queues[course_id] for course_id in rotation):
            active = [course_id for course_id in rotation if queues[course_id]]
            alternatives = [course_id for course_id in active if course_id not in used_courses]
            candidates = alternatives or active
            selected = next((rotation[(cursor + offset) % len(rotation)] for offset in range(len(rotation)) if rotation[(cursor + offset) % len(rotation)] in candidates), candidates[0])
            cursor = (rotation.index(selected) + 1) % len(rotation)
            pending = queues[selected][0]
            chunk = min(pending.remaining, remaining_day, max_session_minutes)
            demand = pending.demand
            scheduled.append(ScheduledActivity(
                demand_id=demand.demand_id,
                course_id=demand.course_id,
                course_code=demand.course_code,
                course_title=demand.course_title,
                concept_id=demand.concept_id,
                concept_name=demand.concept_name,
                syllabus_version_id=demand.syllabus_version_id,
                unit_label=demand.unit_label,
                source_page=demand.source_page,
                assessment_scope=demand.assessment_scope,
                activity_type=demand.activity_type,
                modality=demand.modality,
                scheduled_date=study_date,
                minutes=chunk,
                reason=demand.reason,
                evidence_question_ids=demand.evidence_question_ids,
            ))
            pending.remaining -= chunk
            remaining_day -= chunk
            used_courses.add(selected)
            if pending.remaining == 0:
                queues[selected].popleft()
        if not any(queues[course_id] for course_id in rotation):
            break

    segment_counts: dict[str, int] = {}
    segment_seen: dict[str, int] = {}
    for item in scheduled:
        segment_counts[item.demand_id] = segment_counts.get(item.demand_id, 0) + 1
    result: list[ScheduledActivity] = []
    for item in scheduled:
        segment_seen[item.demand_id] = segment_seen.get(item.demand_id, 0) + 1
        count = segment_counts[item.demand_id]
        reason = item.reason if count == 1 else f"{item.reason} · study segment {segment_seen[item.demand_id]} of {count}"
        result.append(replace(item, reason=reason))
    return result
