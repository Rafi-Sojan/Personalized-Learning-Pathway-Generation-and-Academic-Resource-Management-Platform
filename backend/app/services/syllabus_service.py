"""Conservative, source-aware topic extraction for syllabus text."""

from __future__ import annotations

import re
from dataclasses import dataclass, field


_PAGE_MARKER = re.compile(r"^\s*\[\[PAGE\s+(\d+)\]\]\s*$", re.IGNORECASE)
_CODE_TOKEN = r"(?:\d{2}[A-Z]{2,4}\d{2,3}|[A-Z]{2,3}\d{3}[A-Z]{0,3})"
_COURSE_CODE_LINE = re.compile(rf"\bCOURSE\s+CODE\s*:?\s*({_CODE_TOKEN})\b", re.IGNORECASE)
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
    lines: list[tuple[str, int | None]] = field(default_factory=list)


def extract_declared_course_codes(text: str) -> set[str]:
    """Return normalized course codes printed explicitly in a syllabus or question paper."""
    codes: set[str] = set()
    for raw_line in text.splitlines():
        line = re.sub(r"\s+", " ", raw_line).strip()
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
    matches: list[tuple[int, str]] = []
    for index, line in enumerate(lines):
        marker = _COURSE_CODE_LINE.search(line)
        if marker:
            matches.append((index, re.sub(r"[^A-Z0-9]", "", marker.group(1).upper())))
    if not matches:
        return None
    target = re.sub(r"[^A-Z0-9]", "", course_code.upper())
    for match_index, (start, code) in enumerate(matches):
        if code != target:
            continue
        end = matches[match_index + 1][0] if match_index + 1 < len(matches) else len(lines)
        page_marker = next((position for position in range(start - 1, -1, -1) if _PAGE_MARKER.match(lines[position])), start)
        previous_course = next((position for position, _ in matches if position < start), None)
        if previous_course is not None and previous_course > page_marker:
            page_marker = start
        return "\n".join(lines[page_marker:end])
    return ""


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
    for raw_line in text.splitlines():
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
    has_unit_headings = any(_UNIT_HEADING.match(re.sub(r"\s+", " ", line).strip()) for line in text.splitlines())
    if not has_unit_headings:
        current_block = _UnitBlock("", None)
        blocks.append(current_block)

    for raw_line in text.splitlines():
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
            label = " ".join(part for part in (number.upper(), title.strip(" :-")) if part)[:120]
            current_block = _UnitBlock(label, float(raw_hours) if raw_hours else None)
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


def _append_topic(topics: list[SyllabusTopic], seen: set[str], name: str, unit: str | None, page: int | None, record_type: str, parent: str | None, hours: float | None, limit: int) -> None:
    """Append a unique topic candidate and retain its source hierarchy."""
    normalized = re.sub(r"\s+", " ", name).casefold().strip(" .:-")
    identity = f"{unit or ''}|{parent or ''}|{normalized}"
    if _valid_topic(name, set()) and identity not in seen and len(topics) < limit:
        seen.add(identity)
        topics.append(SyllabusTopic(name.strip(), unit, page, record_type, parent, hours))


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
                    _append_topic(topics, seen, candidate, block.label or None, page, "topic", None, block.hours, limit)
            if len(topics) >= limit:
                return
        return

    prefix = _normalize_topic(body[: matches[0].start()])
    if prefix and _valid_topic(prefix, ignored):
        _append_topic(topics, seen, prefix, block.label or None, block.lines[0][1], "topic", None, block.hours, limit)

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
            _append_topic(topics, seen, heading, block.label or None, page, "subtopic" if parent else "topic", parent, block.hours, limit)
            if not nested:
                active_root = heading
        detail_parent = active_root if is_generic_heading else heading
        details_end = matches[index + 1].start() if index + 1 < len(matches) else len(body)
        details = re.sub(r"\s*\n\s*", " ", body[match.end() : details_end])
        for raw_candidate in re.split(r"\s*[,;]\s*|\.\s+(?=[A-Z])", details):
            candidate = _normalize_topic(raw_candidate)
            if candidate.casefold() in generic_details or not _valid_topic(candidate, ignored):
                continue
            _append_topic(topics, seen, candidate, block.label or None, page, "subtopic", detail_parent, block.hours, limit)
            if len(topics) >= limit:
                return


def extract_topics(text: str) -> list[str]:
    """Return topic names for callers that do not need source provenance."""
    return [topic.name for topic in extract_syllabus_topics(text, limit=100)]
