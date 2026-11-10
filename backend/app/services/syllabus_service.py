"""Conservative, source-aware topic extraction for syllabus text."""

from __future__ import annotations

import re
from dataclasses import dataclass, field


_PAGE_MARKER = re.compile(r"^\s*\[\[PAGE\s+(\d+)\]\]\s*$", re.IGNORECASE)
_CODE_TOKEN = r"(?:\d{2}[A-Z]{2,4}\d{2,3}|[A-Z]{2,3}\d{3}[A-Z]{0,3})"
_COURSE_CODE_LINE = re.compile(rf"\bCOURSE\s+CODE\s*:?\s*({_CODE_TOKEN})\b", re.IGNORECASE)
_COURSE_CODE_PREFIX = re.compile(r"\bCOURSE\s+CODE\s*:?", re.IGNORECASE)
_PARENTHESIZED_CODE = re.compile(rf"\(({_CODE_TOKEN})\)", re.IGNORECASE)
_STANDALONE_CODE = re.compile(rf"^\s*({_CODE_TOKEN})\s*$", re.IGNORECASE)
_UNIT_HEADING = re.compile(
    r"^\s*(?:UNIT|MODULE|CHAPTER)\s*[-–—�\s]*\s*([IVXLCDM]+|\d+)"
    r"\s*[:.]?\s*(.*?)\s*(?:(\d+(?:\.\d+)?)\s*(?:HRS?|HOURS?))?\s*[.]?\s*$",
    re.IGNORECASE,
)
_LEADING_MARKER = re.compile(r"^\s*(?:(?:\d+(?:\.\d+)*|[a-zA-Z][.)]|[-•▪◦])\s*[.)\-:]?\s*)+")
_COURSE_METADATA = re.compile(
    r"\b(?:course code|course title|course name|teaching hours|contact hours|credits?|"
    r"prerequisites?|course outcomes?|course objectives?|assessment|examination scheme|"
    r"semester|category|CIE|SEE|duration|program|rubric|course outcomes?|laboratory experiments)\b",
    re.IGNORECASE,
)
_TOPIC_STOP = re.compile(
    r"^(?:laboratory\s+component|list\s+of\s+laboratory|course\s+outcomes?|reference\s+books?|"
    r"text\s+books?|rubric\s*for|rubric\s+for|assessment\s*:|cie\s+assessment|see\s+assessment)",
    re.IGNORECASE,
)
_TOPIC_HEADING = re.compile(
    r"(?:^|\n|(?<=[.;])\s+|(?<=,)\s+)([A-Z][A-Za-z0-9/&()'’+\- \t]{2,90}?):\s*"
)


@dataclass(frozen=True)
class SyllabusTopic:
    """A topic candidate with the unit and printed PDF page where it was found."""

    name: str
    unit_label: str | None
    source_page: int | None
    record_type: str = "topic"
    parent_label: str | None = None
    unit_hours: float | None = None
    unit_sequence: int | None = None


@dataclass(frozen=True)
class SyllabusUnitProfile:
    """Describe one ordered unit and its source-declared assessment scope."""

    sequence: int
    label: str
    title: str
    hours: float | None
    source_page: int | None
    assessment_scope: str = "both"


@dataclass(frozen=True)
class SyllabusCourseProfile:
    """Contain bounded course-level workload and assessment facts used by roadmaps."""

    course_codes: tuple[str, ...]
    course_type: str
    category: str | None
    credit_allocation: dict[str, float]
    modality_hours: dict[str, float]
    units: tuple[SyllabusUnitProfile, ...]
    course_outcomes: tuple[str, ...]
    assessment_components: tuple[str, ...]
    assessment_format: str
    cie_marks: str | None
    see_marks: str | None
    issues: tuple[str, ...]

    @property
    def has_planning_metadata(self) -> bool:
        """Return whether source evidence is rich enough to justify a reviewable profile."""
        return bool(self.course_codes or self.units or self.modality_hours or self.category)

    def to_dict(self) -> dict[str, object]:
        """Serialize the profile into the stable JSON contract persisted with a syllabus version."""
        return {
            "course_codes": list(self.course_codes),
            "course_type": self.course_type,
            "category": self.category,
            "credit_allocation": dict(self.credit_allocation),
            "modality_hours": dict(self.modality_hours),
            "units": [
                {
                    "sequence": unit.sequence,
                    "label": unit.label,
                    "title": unit.title,
                    "hours": unit.hours,
                    "source_page": unit.source_page,
                    "assessment_scope": unit.assessment_scope,
                }
                for unit in self.units
            ],
            "course_outcomes": list(self.course_outcomes),
            "assessment_components": list(self.assessment_components),
            "assessment_format": self.assessment_format,
            "cie_marks": self.cie_marks,
            "see_marks": self.see_marks,
            "issues": list(self.issues),
        }


@dataclass(frozen=True)
class SyllabusFact:
    """A source line describing outcomes, laboratory work, metadata, or assessment policy."""

    record_type: str
    source_text: str
    source_page: int | None
    unit_label: str | None = None
    hours: float | None = None


@dataclass(frozen=True)
class PrerequisiteCandidate:
    """An explicit prerequisite statement kept separate until human approval."""

    concept_name: str
    prerequisite_name: str
    source_text: str
    source_page: int | None


@dataclass
class _UnitBlock:
    """Mutable source lines collected for one printed syllabus unit."""

    label: str
    hours: float | None
    sequence: int | None = None
    lines: list[tuple[str, int | None]] = field(default_factory=list)


def _course_codes_near_line(lines: list[str], index: int) -> tuple[str, ...]:
    """Read slash-separated aliases from a course-code line and at most two wrapped continuations."""
    wrapped_label = (
        lines[index].strip().casefold() == "course"
        and index + 1 < len(lines)
        and re.match(r"^\s*code\s*:", lines[index + 1], re.I) is not None
    )
    fragments = [lines[index], lines[index + 1]] if wrapped_label else [lines[index]]
    continuation_start = index + 2 if wrapped_label else index + 1
    for continuation in lines[continuation_start : continuation_start + 3]:
        if _PAGE_MARKER.match(continuation) or _COURSE_CODE_PREFIX.search(continuation):
            break
        fragments.append(continuation)
        if re.search(r"\b(?:CIE|Credits?|Semester|Category)\b", continuation, re.I):
            break
    joined = " ".join(fragments)
    code_region = _COURSE_CODE_PREFIX.split(joined, maxsplit=1)[-1]
    code_region = re.split(r"\b(?:CIE|Credits?|Semester|Category)\b", code_region, maxsplit=1, flags=re.I)[0]
    values: list[str] = []
    for match in re.finditer(_CODE_TOKEN, code_region, re.I):
        code = re.sub(r"[^A-Z0-9]", "", match.group(0).upper())
        if code not in values:
            values.append(code)
    return tuple(values)


def _starts_course_code(lines: list[str], index: int) -> bool:
    """Recognize both ordinary and PDF-wrapped `Course` / `Code` label lines."""
    if _COURSE_CODE_PREFIX.search(lines[index]):
        return True
    return (
        lines[index].strip().casefold() == "course"
        and index + 1 < len(lines)
        and re.match(r"^\s*code\s*:", lines[index + 1], re.I) is not None
    )


def extract_declared_course_codes(text: str) -> set[str]:
    """Return normalized course codes printed explicitly in a syllabus or question paper."""
    codes: set[str] = set()
    lines = text.splitlines()
    for index, raw_line in enumerate(lines):
        line = re.sub(r"\s+", " ", raw_line).strip()
        if _starts_course_code(lines, index):
            codes.update(_course_codes_near_line(lines, index))
        for pattern in (_COURSE_CODE_LINE, _PARENTHESIZED_CODE, _STANDALONE_CODE):
            for match in pattern.finditer(line):
                codes.add(re.sub(r"[^A-Z0-9]", "", match.group(1).upper()))
    return codes


def select_syllabus_course_section(text: str, course_code: str) -> str | None:
    """Select one course-code section from a combined RVCE scheme PDF.

    Return the full text when the document has no course-code markers, the
    matching page-preserving section when found, or an empty string when the
    document is multi-course and the requested subject is absent.
    """
    lines = text.splitlines()
    matches: list[tuple[int, tuple[str, ...]]] = []
    for index, line in enumerate(lines):
        if _starts_course_code(lines, index):
            codes = _course_codes_near_line(lines, index)
            if codes:
                matches.append((index, codes))
    if not matches:
        return None
    target = re.sub(r"[^A-Z0-9]", "", course_code.upper())
    for match_index, (start, codes) in enumerate(matches):
        if target not in codes:
            continue
        end = matches[match_index + 1][0] if match_index + 1 < len(matches) else len(lines)
        page_marker = next((position for position in range(start - 1, -1, -1) if _PAGE_MARKER.match(lines[position])), start)
        previous_course = next((position for position, _codes in reversed(matches) if position < start), None)
        if previous_course is not None and previous_course > page_marker:
            page_marker = start
        return "\n".join(lines[page_marker:end])
    return ""


def _clean_profile_line(value: str) -> str:
    """Normalize common PDF text-layer spacing artifacts without changing academic terms."""
    value = re.sub(r"\s+", " ", value).strip()
    replacements = {
        "T otal": "Total",
        "F or": "For",
        "T heory": "Theory",
        "Y oga": "Yoga",
        "W eb": "Web",
        "V ector": "Vector",
        "F undamentals": "Fundamentals",
    }
    for source, replacement in replacements.items():
        value = value.replace(source, replacement)
    return value


def _coalesced_lines(text: str) -> list[str]:
    """Join unit labels split across PDF text columns while preserving page-marker boundaries."""
    source = text.splitlines()
    result: list[str] = []
    index = 0
    while index < len(source):
        line = _clean_profile_line(source[index])
        if re.match(r"^Unit(?:\s*[-–—]\s*[IVXLCDM\d]+)?\s*$", line, re.I):
            fragments = [line]
            cursor = index + 1
            while cursor < len(source) and cursor <= index + 3 and not _PAGE_MARKER.match(source[cursor]):
                fragments.append(_clean_profile_line(source[cursor]))
                cursor += 1
                if re.search(r"\b(?:Hrs?|Hours?)\b", " ".join(fragments), re.I):
                    break
            combined = _clean_profile_line(" ".join(fragments))
            if _UNIT_HEADING.match(combined):
                result.append(combined)
                index = cursor
                continue
        result.append(source[index])
        index += 1
    return result


def _profile_lines(text: str) -> list[tuple[str, int | None]]:
    """Return normalized non-empty text lines paired with the active PDF page marker."""
    result: list[tuple[str, int | None]] = []
    page: int | None = None
    for raw_line in _coalesced_lines(text):
        marker = _PAGE_MARKER.match(raw_line)
        if marker:
            page = int(marker.group(1))
            continue
        line = _clean_profile_line(raw_line)
        if line:
            result.append((line, page))
    return result


def _course_type(course_code: str, course_title: str, category: str | None, credit_allocation: dict[str, float], text: str) -> str:
    """Classify the activity template from explicit title, category, and practical evidence."""
    evidence = " ".join((course_code, course_title, category or "", text[:5000])).casefold()
    if "idea lab" in evidence or "idea development, evaluation" in evidence:
        return "project"
    if "engineering graphics" in evidence or "aided engineering graphics" in evidence:
        return "cad"
    if "yoga" in evidence or course_code.upper() in {"HS115YL", "HS125YL"}:
        return "health_practice"
    if "communicative english" in evidence or "kannada" in evidence:
        return "language"
    if "indian constitution" in evidence:
        return "objective_hss"
    if "programming" in evidence or course_code.upper().startswith(("CS115", "CI115", "AI115", "IS115", "CS125", "CI125", "AI125", "IS125", "CS222")):
        return "programming"
    if course_code.upper().startswith("MA") or "mathematics" in evidence or "engineering mechanics" in evidence:
        return "numerical_theory"
    if credit_allocation.get("practical", 0) > 0 or "theory and practice" in evidence or "theory+lab" in evidence:
        return "theory_lab"
    return "theory"


def _course_outcomes(text: str) -> tuple[str, ...]:
    """Extract labeled outcomes while retaining their wording and avoiding rubric tails."""
    cleaned = re.sub(r"\[\[PAGE\s+\d+\]\]", " ", text, flags=re.I)
    outcomes: list[str] = []
    lines = cleaned.splitlines()
    for index, line in enumerate(lines):
        match = re.match(r"^\s*(CO\s*\d+)\s+(.+)$", _clean_profile_line(line), re.I)
        if not match:
            continue
        value = f"{re.sub(r'\s+', '', match.group(1).upper())} {match.group(2).strip()}"
        for continuation in lines[index + 1 : index + 4]:
            next_line = _clean_profile_line(continuation)
            if not next_line or re.match(r"^(?:CO\s*\d+|Reference Books?|RUBRIC|Text Books?)\b", next_line, re.I):
                break
            if re.match(r"^(?:Semester|Category|Course Code|Credits|Total Hours)\b", next_line, re.I):
                break
            value = f"{value} {next_line}"
        normalized = re.sub(r"\s+", " ", value).strip()
        normalized = re.sub(r"\s+[A-Za-z ]+Courses?\s+Page\s+\d+\s*$", "", normalized, flags=re.I)[:1000]
        if normalized not in outcomes:
            outcomes.append(normalized)
    return tuple(outcomes[:20])


def extract_course_profile(text: str, course_code: str = "", course_title: str = "") -> SyllabusCourseProfile:
    """Extract a bounded, reviewable workload and assessment profile from one course section."""
    lines = _profile_lines(text)
    course_codes = tuple(sorted(extract_declared_course_codes(text)))
    category: str | None = None
    credit_allocation = {"lecture": 0.0, "tutorial": 0.0, "practical": 0.0}
    modality_hours = {"lecture": 0.0, "tutorial": 0.0, "practical": 0.0, "experiential": 0.0}
    cie_marks: str | None = None
    see_marks: str | None = None
    total_hours_seen = False
    units: list[SyllabusUnitProfile] = []
    for index, (line, page) in enumerate(lines):
        window = _clean_profile_line(" ".join(item[0] for item in lines[index : index + 4]))
        category_match = re.search(
            r"\bCategory\s*:\s*(.+?)(?=\s+(?:Stream|CIE|SEE|Course(?:\s+(?:Code|Title|Name))?|Credits?|Total\s+Hours)\b|$)",
            window,
            re.I,
        )
        if category_match and category is None:
            category = category_match.group(1).strip()[:120]
        credit_match = re.search(
            r"\bCredits?\s*:?\s*(?:(?:L\s*:\s*T\s*:\s*P)|(?:L\s*-\s*T\s*-\s*P))\s*:\s*(\d+(?:\.\d+)?)\s*[:\-]\s*(\d+(?:\.\d+)?)\s*[:\-]\s*(\d+(?:\.\d+)?)",
            window,
            re.I,
        )
        if credit_match and not any(credit_allocation.values()):
            credit_allocation = {
                "lecture": float(credit_match.group(1)),
                "tutorial": float(credit_match.group(2)),
                "practical": float(credit_match.group(3)),
            }
        total_match = re.search(r"\bTotal\s+Hours\s*:\s*(.+?)(?=\s+SEE\b|$)", window, re.I)
        if total_match and not total_hours_seen:
            for hours, suffix in re.findall(r"(\d+(?:\.\d+)?)\s*(EL|L|T|P)\b", total_match.group(1), re.I):
                key = {"L": "lecture", "T": "tutorial", "P": "practical", "EL": "experiential"}[suffix.upper()]
                modality_hours[key] += float(hours)
            total_hours_seen = any(modality_hours.values())
        if cie_marks is None:
            cie_match = re.search(r"\bCIE\s*:\s*(\d+(?:\s*\+\s*\d+)*)\s*Marks?", window, re.I)
            if cie_match:
                cie_marks = re.sub(r"\s+", "", cie_match.group(1))
        if see_marks is None:
            see_match = re.search(r"\bSEE\s*:\s*(\d+(?:\s*\+\s*\d+)*)\s*Marks?", window, re.I)
            if see_match:
                see_marks = re.sub(r"\s+", "", see_match.group(1))
        unit_match = _UNIT_HEADING.match(line)
        if unit_match:
            number, raw_title, raw_hours = unit_match.groups()
            title = raw_title.strip(" :-")
            assessment_scope = "cie_only" if re.search(r"For\s+CIE\s+Only", title, re.I) else "both"
            title = re.sub(r"\(?\s*For\s+CIE\s+Only\s*\)?", "", title, flags=re.I).strip(" :-")
            label = number.upper()
            units.append(SyllabusUnitProfile(len(units) + 1, label, title, float(raw_hours) if raw_hours else None, page, assessment_scope))

    components: list[str] = []
    component_patterns = (
        ("quiz", r"\bQUIZ(?:ZES)?\b"),
        ("test", r"\bTESTS?\b"),
        ("experiential_learning", r"\bEXPERIENTIAL\s+LEARNING\b"),
        ("module_completion", r"\bMODULE\s+COMPLETION\b"),
        ("laboratory", r"\b(?:LABORATORY|LAB\s+TEST|LAB\s+EXPERIMENT)\b"),
        ("project", r"\bPROJECT(?:\s+BASED)?\b"),
        ("demonstration", r"\bDEMONSTRATION\b"),
    )
    for name, pattern in component_patterns:
        if re.search(pattern, text, re.I):
            components.append(name)
    if re.search(r"Objective\s+type\s+questions?\s+covering\s+entire\s+syllabus", text, re.I) and not re.search(r"\bPart\s*[- ]?B\b", text, re.I):
        assessment_format = "objective_only"
    elif "demonstration" in components:
        assessment_format = "demonstration"
    elif re.search(r"problem\s*/?\s*project\s+based", text, re.I):
        assessment_format = "project"
    elif re.search(r"\bPart\s*[- ]?B\b", text, re.I):
        assessment_format = "unitwise_theory"
    elif credit_allocation.get("practical", 0) > 0:
        assessment_format = "theory_practical"
    else:
        assessment_format = "theory"

    resolved_code = course_code or (course_codes[0] if course_codes else "")
    profile_type = _course_type(resolved_code, course_title, category, credit_allocation, text)
    issues: list[str] = []
    if not units:
        issues.append("No ordered unit structure was detected; verify the source text before scheduling.")
    if not any(modality_hours.values()):
        issues.append("No explicit Total Hours allocation was detected; roadmap time will use unit or difficulty fallback estimates.")
    unit_total = sum(unit.hours or 0.0 for unit in units)
    declared_total = sum(modality_hours.values())
    comparable_totals = [value for value in modality_hours.values() if value > 0]
    if declared_total > 0:
        comparable_totals.append(declared_total)
    if unit_total > 0 and comparable_totals and not any(abs(unit_total - value) <= 0.5 for value in comparable_totals):
        issues.append(f"Unit hours total {unit_total:g}, which does not reconcile with the declared modality totals; reviewer confirmation is required.")
    credits = sum(credit_allocation.values())
    if credits > 0 and declared_total > 0 and declared_total < credits * 15:
        issues.append("Declared workload is unusually low for the printed L:T:P allocation; verify the detailed header against the scheme table.")
    return SyllabusCourseProfile(
        course_codes=course_codes,
        course_type=profile_type,
        category=category,
        credit_allocation=credit_allocation,
        modality_hours=modality_hours,
        units=tuple(units),
        course_outcomes=_course_outcomes(text),
        assessment_components=tuple(components),
        assessment_format=assessment_format,
        cie_marks=cie_marks,
        see_marks=see_marks,
        issues=tuple(issues),
    )


def extract_syllabus_facts(text: str, limit: int = 500) -> list[SyllabusFact]:
    """Collect clearly labeled syllabus metadata without treating it as topic nodes."""
    patterns = (
        ("outcome", re.compile(r"\b(?:course outcomes?|learning outcomes?|CO\s*\d+)\b", re.I)),
        ("lab", re.compile(r"\b(?:laboratory|lab work|practical work|experiments?)\b", re.I)),
        ("metadata", re.compile(r"\b(?:course code|course title|semester|scheme|credits?|contact hours|teaching hours|prerequisites?)\b", re.I)),
        ("assessment", re.compile(r"\b(?:assessment|CIE|SEE|quiz|question paper|examination scheme|marks distribution)\b", re.I)),
    )
    facts: list[SyllabusFact] = []
    page: int | None = None
    seen: set[tuple[str, str]] = set()
    unit: str | None = None
    in_lab_list = False
    in_assessment_rubric = False
    for raw_line in _coalesced_lines(text):
        marker = _PAGE_MARKER.match(raw_line)
        if marker:
            page = int(marker.group(1))
            continue
        line = re.sub(r"\s+", " ", raw_line).strip()
        if len(line) < 5 or len(line) > 500:
            continue
        unit_heading = _UNIT_HEADING.match(line)
        if unit_heading:
            number, title, raw_hours = unit_heading.groups()
            unit = " ".join(part for part in (number.upper(), title.strip(" :-")) if part)[:120]
            hours = float(raw_hours) if raw_hours else None
            identity = ("unit", line.casefold())
            if identity not in seen:
                seen.add(identity)
                facts.append(SyllabusFact("unit", line, page, unit, hours))
            continue
        if re.search(r"list of laboratory experiments|laboratory experiments", line, re.I):
            in_lab_list = True
        if re.search(r"rubric for .*examination", line, re.I):
            in_assessment_rubric = True
        if in_lab_list and re.match(r"^(?:PART\s*[- ]?B|COURSE OUTCOMES|RUBRIC FOR)", line, re.I):
            in_lab_list = False
        if in_assessment_rubric and re.match(r"^(?:COURSE OUTCOMES|UNIT\s*[- ]?I\b)", line, re.I):
            in_assessment_rubric = False
        is_course_title = (
            line.isupper()
            and len(re.sub(r"[^A-Z]", "", line)) >= 8
            and not re.search(r"\b(?:RUBRIC|PART|COURSE OUTCOMES|LABORATORY|COURSE CODE|TOTAL)\b", line)
        )
        if is_course_title:
            identity = ("course_title", line.casefold())
            if identity not in seen:
                seen.add(identity)
                facts.append(SyllabusFact("course_title", line, page, unit))
            continue
        selected_type = "lab" if in_lab_list else "assessment" if in_assessment_rubric and re.search(r"\b(?:PART\s*[A-Z]|objective type|unit\s*[IVX0-9]|marks|total)\b", line, re.I) else None
        if selected_type:
            identity = (selected_type, line.casefold())
            if identity not in seen:
                seen.add(identity)
                facts.append(SyllabusFact(selected_type, line, page, unit))
            continue
        for record_type, pattern in patterns:
            if pattern.search(line):
                identity = (record_type, line.casefold())
                if identity not in seen:
                    seen.add(identity)
                    facts.append(SyllabusFact(record_type, line, page, unit))
                break
        if len(facts) >= limit:
            break
    return facts


def extract_prerequisite_candidates(text: str, limit: int = 100) -> list[PrerequisiteCandidate]:
    """Extract only explicitly labeled or stated prerequisite relationships."""
    patterns = (
        re.compile(r"^\s*prerequisites?\s+for\s+(.+?)\s*[:\-]\s*(.+?)\s*[.;]?\s*$", re.I),
        re.compile(r"^\s*(.+?)\s+(?:requires|depends on)\s+(.+?)\s*[.;]?\s*$", re.I),
    )
    candidates: list[PrerequisiteCandidate] = []
    page: int | None = None
    for raw_line in text.splitlines():
        marker = _PAGE_MARKER.match(raw_line)
        if marker:
            page = int(marker.group(1))
            continue
        line = re.sub(r"\s+", " ", raw_line).strip()
        for pattern in patterns:
            match = pattern.match(line)
            if match and 3 <= len(match.group(1)) <= 180 and 3 <= len(match.group(2)) <= 180:
                candidates.append(PrerequisiteCandidate(match.group(1).strip(), match.group(2).strip(), line, page))
                break
        if len(candidates) >= limit:
            break
    return candidates


def extract_syllabus_topics(text: str, limit: int = 300) -> list[SyllabusTopic]:
    """Build unit/topic/subtopic candidates from the teaching-content portion of a syllabus."""
    topics: list[SyllabusTopic] = []
    seen: set[str] = set()
    page: int | None = None
    blocks: list[_UnitBlock] = []
    current_block: _UnitBlock | None = None
    skip_contents = False
    contents_page: int | None = None
    ignored = {"contents", "table of contents", "syllabus", "course outcomes", "course objectives", "index"}
    source_lines = _coalesced_lines(text)
    has_unit_headings = any(_UNIT_HEADING.match(re.sub(r"\s+", " ", line).strip()) for line in source_lines)
    if not has_unit_headings:
        current_block = _UnitBlock("", None, None)
        blocks.append(current_block)

    for raw_line in source_lines:
        marker = _PAGE_MARKER.match(raw_line)
        if marker:
            next_page = int(marker.group(1))
            if skip_contents and contents_page is not None and next_page != contents_page:
                skip_contents = False
            page = next_page
            continue
        line = re.sub(r"\s+", " ", raw_line).strip()
        if not line:
            continue
        key = line.casefold().strip(" .:-")
        if key in {"contents", "table of contents", "index"} or re.search(r"COURSE CODE\s+COURSE TITLE|INDEX\s+(?:THIRD|FOURTH) SEMESTER", line, re.I):
            skip_contents = True
            contents_page = page
            continue
        if skip_contents:
            # A syllabus section heading ends the contents block; until then avoid
            # turning page-numbered index entries into teaching topics.
            if page is None and re.match(r"^(?:UNIT|MODULE|CHAPTER)\b", line, re.IGNORECASE):
                skip_contents = False
            else:
                continue

        heading = _UNIT_HEADING.match(line)
        if heading:
            number, title, raw_hours = heading.groups()
            normalized_title = _clean_profile_line(title).strip(" :-")
            label = " ".join(part for part in (number.upper(), normalized_title) if part)[:120]
            current_block = _UnitBlock(label, float(raw_hours) if raw_hours else None, len(blocks) + 1)
            blocks.append(current_block)
            if title.strip() and _valid_topic(title.strip(), ignored):
                current_block.lines.append((f"{title.strip(' :-')}:", page))
            continue

        if _TOPIC_STOP.match(line):
            current_block = None if has_unit_headings else current_block
            continue
        if current_block is None:
            continue
        if re.fullmatch(r"Artificial Intelligence and Machine Learning\s+\d+", line, re.I):
            continue
        if _COURSE_METADATA.search(line) or re.search(r"\b(?:ISBN|https?://|www\.)\b", line, re.I):
            continue
        current_block.lines.append((line, page))

    for block in blocks:
        _parse_unit_block(block, topics, seen, ignored, limit)
        if len(topics) >= limit:
            break
    return topics


def _valid_topic(candidate: str, ignored: set[str]) -> bool:
    """Reject short, administrative, or course-identity lines as topic nodes."""
    normalized = candidate.casefold().strip(" .:-")
    words = re.findall(r"[A-Za-z0-9]+", candidate)
    return not (
        len(candidate) < 4 or len(candidate) > 140 or len(words) > 18 or normalized.isdigit() or normalized in ignored
        or _COURSE_METADATA.search(candidate) or re.fullmatch(r"[A-Z]{1,5}\s*\d{2,}[A-Z0-9]*", candidate)
        or re.search(r"\b(?:ISBN|https?://|www\.|MAXIMUM MARKS|COMPONENTS MARKS)\b", candidate, re.I)
        or re.match(r"^(?:CO|PO|PSO)\s*\d+\b", candidate, re.I)
        or sum(character.isdigit() for character in candidate) > max(4, len(candidate) // 4)
    )


def _append_topic(topics: list[SyllabusTopic], seen: set[str], name: str, unit: str | None, page: int | None, record_type: str, parent: str | None, hours: float | None, sequence: int | None, limit: int) -> None:
    """Append a unique topic candidate and retain its source hierarchy."""
    normalized = re.sub(r"\s+", " ", name).casefold().strip(" .:-")
    identity = f"{unit or ''}|{parent or ''}|{normalized}"
    if _valid_topic(name, set()) and identity not in seen and len(topics) < limit:
        seen.add(identity)
        topics.append(SyllabusTopic(name.strip(), unit, page, record_type, parent, hours, sequence))


def _normalize_topic(value: str) -> str:
    """Remove list markers and OCR spacing artifacts around punctuation from one candidate."""
    value = _LEADING_MARKER.sub("", value).strip(" \t:-•▪◦")
    value = re.sub(r"\s+", " ", value)
    value = re.sub(r"\s+([,.;:)])", r"\1", value)
    return re.sub(r"^(?:and|or)\s+", "", value, flags=re.I).strip(" .:-")


def _page_for_heading(lines: list[tuple[str, int | None]], heading: str) -> int | None:
    """Locate the first source page containing a normalized heading fragment."""
    needle = re.sub(r"\s+", " ", heading).casefold()
    for line, page in lines:
        if needle in re.sub(r"\s+", " ", line).casefold():
            return page
    return lines[0][1] if lines else None


def _parse_unit_block(block: _UnitBlock, topics: list[SyllabusTopic], seen: set[str], ignored: set[str], limit: int) -> None:
    """Convert a unit's wrapped prose into heading nodes and comma-delimited child nodes."""
    if not block.lines or len(topics) >= limit:
        return
    body = "\n".join(line for line, _ in block.lines)
    matches = list(_TOPIC_HEADING.finditer(body))
    if not matches:
        for line, page in block.lines:
            for raw_candidate in re.split(r"\s*[;,]\s*", line):
                candidate = _normalize_topic(raw_candidate)
                if _valid_topic(candidate, ignored):
                    _append_topic(topics, seen, candidate, block.label or None, page, "topic", None, block.hours, block.sequence, limit)
            if len(topics) >= limit:
                return
        return

    prefix = _normalize_topic(body[: matches[0].start()])
    if prefix and _valid_topic(prefix, ignored):
        _append_topic(topics, seen, prefix, block.label or None, block.lines[0][1], "topic", None, block.hours, block.sequence, limit)

    generic_details = {"introduction", "overview", "example", "examples", "case study", "case studies"}
    active_root: str | None = None
    for index, match in enumerate(matches):
        heading = _normalize_topic(match.group(1))
        if not _valid_topic(heading, ignored):
            continue
        page = _page_for_heading(block.lines, heading)
        boundary = body[match.start() : match.start(1)]
        preceding = body[: match.start()].rstrip()[-1:] if match.start() else ""
        nested = active_root is not None and "\n" not in boundary and preceding == ","
        is_generic_heading = heading.casefold() in {"example", "examples", "overview"}
        if not is_generic_heading:
            parent = active_root if nested else None
            _append_topic(topics, seen, heading, block.label or None, page, "subtopic" if parent else "topic", parent, block.hours, block.sequence, limit)
            if not nested:
                active_root = heading
        detail_parent = active_root if is_generic_heading else heading
        details_end = matches[index + 1].start() if index + 1 < len(matches) else len(body)
        details = re.sub(r"\s*\n\s*", " ", body[match.end() : details_end])
        for raw_candidate in re.split(r"\s*[,;]\s*|\.\s+(?=[A-Z])", details):
            candidate = _normalize_topic(raw_candidate)
            if candidate.casefold() in generic_details or not _valid_topic(candidate, ignored):
                continue
            _append_topic(topics, seen, candidate, block.label or None, page, "subtopic", detail_parent, block.hours, block.sequence, limit)
            if len(topics) >= limit:
                return


def extract_topics(text: str) -> list[str]:
    """Return topic names for callers that do not need source provenance."""
    return [topic.name for topic in extract_syllabus_topics(text, limit=100)]
