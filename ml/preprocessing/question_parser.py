"""Parse question papers without mixing answer schemes or administrative text into questions."""

from __future__ import annotations

import re
from dataclasses import dataclass


_PAGE_MARKER = re.compile(r"^\s*\[\[PAGE\s+(\d+)\]\]\s*$", re.IGNORECASE)
_PART_HEADER = re.compile(r"\bPART\s*[-:–—]?\s*([A-D])\b", re.IGNORECASE)
_SOLUTION_HEADER = re.compile(
    r"\b(?:scheme\s*(?:and|&)\s*solutions?|scheme\s+of\s+evaluation|"
    r"model\s+answers?|answer\s+keys?|solutions?\s+and\s+scheme)\b",
    re.IGNORECASE,
)
_QUESTION_PAPER_HEADER = re.compile(r"\b(?:CIE\s*[-:–—]?\s*(?:I{1,3}|\d+)\s*:\s*)?QUESTION\s+PAPER\b", re.IGNORECASE)
_SEE_HEADER = re.compile(r"\b(?:semester\s+end\s+examination|B\.?\s*E\.?\s+Examinations?)\b", re.IGNORECASE)
_CIE_HEADER = re.compile(r"\bCIE\s*[-:–—]?\s*(?:I{1,3}|\d+)\b", re.IGNORECASE)
_INSTRUCTIONS_HEADER = re.compile(r"^\s*Instructions?\s+to\s+(?:the\s+)?candidates?\s*:?\s*$", re.IGNORECASE)
_QUESTION_AREA_STOP = re.compile(
    r"^\s*(?:COURSE\s+OUTCOMES?|CO\s*-?\s*PO\s+MAPPING|BLOOM'?S?\s+TAXONOMY|"
    r"RUBRIC\s+FOR|SCHEME\s*(?:AND|&)\s*SOLUTION)\b",
    re.IGNORECASE,
)
_PAPER_METADATA = re.compile(
    r"^\s*(?:R\.?\s*V\.?\s+COLLEGE|DEPARTMENT\s+OF|COURSE\s*:|\(CODE\)|"
    r"DATE\s*:|DURATION\s*:|STAFF\s*:|NAME\s*:|USN\s*:|SECTION\s*:|"
    r"TIME\s*:|MAXIMUM\s+MARKS\s*:|CIE\b.*QUESTION\s+PAPER|QUESTION\s+PAPER|"
    r"SL\.?\s*NO\.?|Q\.?\s*NO\.?|QUESTIONS?\s+MARKS|"
    r"MARKS?\s+(?:BTL?|L\d)|L1\s+L2\s+L3|ANSWER\s+ALL\s+QUESTIONS)\b",
    re.IGNORECASE,
)
_COLUMN_ONLY_MARKS = re.compile(
    r"^\s*(\d{1,3}(?:\.\d+)?)\s+(?:L?\d|[1-6])(?:\s+(?:CO)?[\d,]+)?\s*$",
    re.IGNORECASE,
)
_INLINE_MARKS_WITH_COLUMNS = re.compile(
    r"\s+(\d{1,3}(?:\.\d+)?)\s+(?:L?\d|[1-6])(?:\s+(?:CO)?[\d,]+)?\s*$",
    re.IGNORECASE,
)
_BRACKETED_MARKS = re.compile(
    r"\s*(?:\((\d+(?:\.\d+)?)\s*(?:marks?|M)?\)|\[(\d+(?:\.\d+)?)\s*(?:marks?|M)?\])\s*$",
    re.IGNORECASE,
)
_PLAIN_MARKS = re.compile(r"\s+(0[1-9]|1\d|20)\s*$")
_FIGURE_CAPTION = re.compile(
    r"^\s*(?:fig(?:ure)?\.?\s*)\d+(?:\.\d+)?(?:\s+(0[1-9]|1\d|20))?\s*$",
    re.IGNORECASE,
)
_IGNORED_SEPARATOR = re.compile(r"^\s*(?:OR|AND|TURN\s+OVER|P\.?T\.?O\.?)\s*$", re.IGNORECASE)


@dataclass(frozen=True)
class ParsedQuestion:
    """A source-located question together with printed section and assessment metadata."""

    prompt: str
    paper_part: str | None
    question_kind: str
    question_number: str | None = None
    subpart: str | None = None
    marks: float | None = None
    source_page: int | None = None
    question_format: str = "unknown"
    assessment_type: str | None = None


@dataclass(frozen=True)
class _QuestionStart:
    """Internal representation of a printed question-number token."""

    number: str
    subpart: str | None
    remainder: str


def _split_pages(text: str) -> list[tuple[int | None, str]]:
    """Split marker-delimited extraction text while preserving unmarked legacy input."""
    pages: list[tuple[int | None, list[str]]] = []
    current_page: int | None = None
    current_lines: list[str] = []
    for line in text.replace("\r\n", "\n").replace("\r", "\n").splitlines():
        marker = _PAGE_MARKER.match(line)
        if marker:
            if current_lines or current_page is not None:
                pages.append((current_page, current_lines))
            current_page = int(marker.group(1))
            current_lines = []
        else:
            current_lines.append(line)
    if current_lines or current_page is not None:
        pages.append((current_page, current_lines))
    return [(page, "\n".join(lines)) for page, lines in pages] or [(None, text)]


def _assessment_from_page(page_text: str, previous: str | None) -> str | None:
    """Use strong printed headers to distinguish CIE/test pages from SEE pages."""
    if _CIE_HEADER.search(page_text) and _QUESTION_PAPER_HEADER.search(page_text):
        return "test"
    if _SEE_HEADER.search(page_text) and re.search(r"\bPART\s*[-:–—]?\s*A\b", page_text, re.IGNORECASE):
        return "see"
    return previous


def _part_from_line(line: str) -> str | None:
    """Read a structural Part heading without reacting to prose that merely mentions a part."""
    match = _PART_HEADER.search(line)
    if match and (line.upper().startswith("PART") or re.match(r"^SL\.?\s*NO", line, re.IGNORECASE)):
        return match.group(1).upper()
    return None


def _question_start(line: str, last_number: str | None, current_part: str | None) -> _QuestionStart | None:
    """Recognize RVCE table numbering, decimal quiz items, and continued subparts."""
    patterns: tuple[tuple[re.Pattern[str], str], ...] = (
        (re.compile(r"^\s*(?:\d{1,2}\s+)?(\d{1,2}\.\d{1,2})\s+(.+)$"), "decimal"),
        (re.compile(r"^\s*(\d{1,2})\s*\.\s*([a-h])(?:\s+|[.)]\s*|$)(.*)$", re.IGNORECASE), "subpart"),
        (re.compile(r"^\s*(\d{1,2})\s*\(([a-h])\)\s*(.*)$", re.IGNORECASE), "subpart"),
        (re.compile(r"^\s*(\d{1,2})([a-h])(?:\s+|[.)]\s*|$)(.*)$", re.IGNORECASE), "subpart"),
        (re.compile(r"^\s*(\d{1,2})\s+([a-h])\s+(.+)$", re.IGNORECASE), "subpart"),
        (re.compile(r"^\s*(?:Q(?:UESTION)?\s*)?(\d{1,2})\s*[.):]\s*(.*)$", re.IGNORECASE), "number"),
        (re.compile(r"^\s*(?:Q(?:UESTION)?\s*)?(\d{1,2})\s+([A-Z_].*)$"), "number"),
    )
    for pattern, kind in patterns:
        match = pattern.match(line)
        if not match:
            continue
        if kind == "decimal":
            return _QuestionStart(match.group(1), None, match.group(2).strip())
        if kind == "subpart":
            return _QuestionStart(match.group(1), match.group(2).lower(), match.group(3).strip())
        return _QuestionStart(match.group(1), None, match.group(2).strip())
    continued = re.match(r"^\s*([a-h])\s+(?=[A-Z_])(.*)$", line)
    if continued and last_number and current_part == "B":
        return _QuestionStart(last_number, continued.group(1).lower(), continued.group(2).strip())
    return None


def _clean_prompt_line(line: str) -> tuple[str, float | None]:
    """Remove mark/BT/CO columns and return any mark value printed on the line."""
    compact = re.sub(r"\s+", " ", line).strip()
    if not compact or _IGNORED_SEPARATOR.match(compact):
        return "", None
    figure = _FIGURE_CAPTION.match(compact)
    if figure:
        return "", float(figure.group(1)) if figure.group(1) else None
    column_only = _COLUMN_ONLY_MARKS.match(compact)
    if column_only:
        return "", float(column_only.group(1))
    for pattern in (_INLINE_MARKS_WITH_COLUMNS, _BRACKETED_MARKS, _PLAIN_MARKS):
        match = pattern.search(compact)
        if match:
            value = next(group for group in match.groups() if group is not None)
            return compact[: match.start()].rstrip(" \t-:"), float(value)
    return compact, None


def parse_question_records(text: str, *, part_a_is_quiz: bool = False) -> list[ParsedQuestion]:
    """Parse printed questions, excluding answer schemes and preserving source coordinates."""
    records: list[ParsedQuestion] = []
    current_part: str | None = None
    current_assessment: str | None = None
    current_lines: list[str] = []
    current_number: str | None = None
    current_subpart: str | None = None
    current_marks: float | None = None
    current_page: int | None = None
    last_major_number: str | None = None
    in_solution_pages = False
    awaiting_part_after_instructions = False

    def flush_question() -> None:
        """Append one normalized question when the active buffer contains a real prompt."""
        nonlocal current_lines, current_marks, current_number, current_subpart
        prompt = re.sub(r"\s+", " ", " ".join(current_lines)).strip(" \t-:")
        if len(prompt) >= 4 and re.search(r"[A-Za-z]", prompt):
            kind = "quiz" if current_part == "A" and part_a_is_quiz else "main"
            records.append(
                ParsedQuestion(
                    prompt=prompt[:20_000],
                    paper_part=current_part,
                    question_kind=kind,
                    question_number=current_number,
                    subpart=current_subpart,
                    marks=current_marks,
                    source_page=current_page,
                    assessment_type=current_assessment,
                )
            )
        current_lines = []
        current_marks = None
        current_number = None
        current_subpart = None

    for page_number, page_text in _split_pages(text.strip()):
        has_solution_header = bool(_SOLUTION_HEADER.search(page_text))
        has_question_header = bool(_QUESTION_PAPER_HEADER.search(page_text)) or bool(
            _SEE_HEADER.search(page_text) and _PART_HEADER.search(page_text)
        )
        if has_solution_header:
            flush_question()
            in_solution_pages = True
            continue
        if has_question_header:
            flush_question()
            in_solution_pages = False
            current_part = None
            last_major_number = None
            awaiting_part_after_instructions = False
        if in_solution_pages:
            continue
        current_assessment = _assessment_from_page(page_text, current_assessment)
        current_page = page_number
        for raw_line in page_text.splitlines():
            line = re.sub(r"\s+", " ", raw_line).strip()
            if not line:
                continue
            if _QUESTION_AREA_STOP.match(line):
                flush_question()
                break
            if _INSTRUCTIONS_HEADER.match(line):
                flush_question()
                awaiting_part_after_instructions = True
                continue
            part = _part_from_line(line)
            if part:
                flush_question()
                current_part = part
                awaiting_part_after_instructions = False
                continue
            if awaiting_part_after_instructions:
                continue
            if _PAPER_METADATA.match(line) or re.search(r"\bSemester\s*:\s*", line, re.IGNORECASE):
                continue
            column_marks = _COLUMN_ONLY_MARKS.match(line)
            if column_marks and current_number is not None:
                current_marks = float(column_marks.group(1))
                continue
            start = _question_start(line, last_major_number, current_part)
            if start:
                flush_question()
                current_number = start.number
                current_subpart = start.subpart
                last_major_number = start.number.split(".", 1)[0]
                cleaned, marks = _clean_prompt_line(start.remainder)
                if cleaned:
                    current_lines.append(cleaned)
                if marks is not None:
                    current_marks = marks
                continue
            if current_number is None:
                continue
            cleaned, marks = _clean_prompt_line(line)
            if cleaned:
                current_lines.append(cleaned)
            if marks is not None:
                current_marks = marks
        flush_question()

    if records:
        return records[:1000]
    return _parse_paragraph_fallback(text, part_a_is_quiz=part_a_is_quiz)


def _parse_paragraph_fallback(text: str, *, part_a_is_quiz: bool = False) -> list[ParsedQuestion]:
    """Split genuinely unnumbered text without treating answer-scheme paragraphs as questions."""
    if _SOLUTION_HEADER.search(text):
        return []
    records: list[ParsedQuestion] = []
    current_part: str | None = None
    for paragraph in re.split(r"\n\s*\n", text):
        lines = [re.sub(r"\s+", " ", line).strip() for line in paragraph.splitlines() if line.strip()]
        if not lines:
            continue
        part = _PART_HEADER.search(lines[0])
        if part:
            current_part = part.group(1).upper()
            lines = lines[1:]
        prompt = " ".join(line for line in lines if not _PAPER_METADATA.match(line)).strip()
        if len(prompt) >= 5 and re.search(r"[A-Za-z]", prompt):
            records.append(
                ParsedQuestion(
                    prompt[:20_000],
                    current_part,
                    "quiz" if current_part == "A" and part_a_is_quiz else "main",
                )
            )
    return records[:1000]


def parse_questions(text: str) -> list[str]:
    """Return prompt strings for callers using the legacy question-parser contract."""
    return [record.prompt for record in parse_question_records(text)]
