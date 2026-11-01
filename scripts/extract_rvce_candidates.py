"""Extract review candidates from the supplied RVCE syllabus PDFs.

Extraction is intentionally conservative: only course-detail pages with an
explicit course code and L:T:P credit tuple become candidates. Every row stays
pending academic review and retains local file/page provenance.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any

from pypdf import PdfReader


ROOT = Path(__file__).resolve().parents[1]
COURSE_CODE = re.compile(r"Course\s+Code\s*:\s*([A-Z]{2,4}\d{3}[A-Z]{2,4})", re.I)
CREDIT_TUPLE = re.compile(r"L\s*:\s*T\s*:\s*P\s*:\s*(\d+)\s*:\s*(\d+)\s*:\s*(\d+)", re.I)
SEMESTER = re.compile(r"Semester\s*[:\-]\s*(I{1,3}|IV|1|2|3|4)\b", re.I)
TITLE = re.compile(r"Semester\s*[:\-]\s*(?:I{1,3}|IV|1|2|3|4)\s+(.+?)\s+Category\s*:", re.I | re.S)
CATEGORY = re.compile(r"Category\s*:\s*([^\r\n]+)", re.I)
TOTAL_HOURS = re.compile(r"Total\s+Hours\s*:\s*(\d+)\s*L(?:\s*\+\s*(\d+)\s*P)?", re.I)


def _semester(value: str | None, fallback: int) -> int:
    """Normalize Roman or Arabic semester labels and use the document range if absent."""
    if value is None:
        return fallback
    return {"I": 1, "II": 2, "III": 3, "IV": 4}.get(value.upper(), int(value) if value.isdigit() else fallback)


def extract_document(source_root: Path, item: dict[str, Any], source_url: str) -> list[dict[str, Any]]:
    """Extract course-detail rows whose code and credit tuple are explicit on a PDF page."""
    path = source_root / item["relative_path"]
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    if digest != item["sha256"]:
        raise ValueError(f"Source changed since inventory: {path}")
    reader = PdfReader(str(path))
    rows: dict[tuple[str, int, str], dict[str, Any]] = {}
    for page_number, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""
        code_match = COURSE_CODE.search(text)
        credit_match = CREDIT_TUPLE.search(text)
        title_match = TITLE.search(text)
        if not (code_match and credit_match and title_match):
            continue
        semester_match = SEMESTER.search(text)
        semester = _semester(semester_match.group(1) if semester_match else None, item["semesters"][0])
        title = " ".join(title_match.group(1).split()).strip(" :-\u2013\u2014")
        credits = sum(int(value) for value in credit_match.groups())
        category_match = CATEGORY.search(text)
        category = " ".join(category_match.group(1).split()).strip() if category_match else ""
        hours_match = TOTAL_HOURS.search(text)
        contact_hours = sum(int(value) for value in hours_match.groups() if value) if hours_match else None
        course_code = code_match.group(1).upper()
        key = (course_code, semester, title.casefold())
        rows[key] = {
            # First-year PDFs contain stream-specific rows but the current
            # extraction does not map each row to a branch. Keep them out of
            # branch enrollment until an academic reviewer resolves scope.
            "program_code": "BE-UNMAPPED" if item["program_code"] == "BE-COMMON" else item["program_code"],
            "scheme_year": item["scheme_year"],
            "semester": semester,
            "course_code": course_code,
            "title": title,
            "credits": credits,
            "category": category[:80],
            "contact_hours": contact_hours,
            "prerequisites": [],
            "outcomes": [],
            "source_url": source_url,
            "source_checksum": digest,
            "verification_status": "pending_review",
            "source_filename": item["relative_path"],
            "source_page": page_number,
        }
    return list(rows.values())


def main() -> int:
    """Verify source fingerprints, extract candidates, and quarantine code/title conflicts."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", type=Path, required=True, help="Folder containing the inventoried RVCE PDFs")
    parser.add_argument("--output", type=Path, default=ROOT / "database" / "rvce_course_candidates.json")
    parser.add_argument("--conflicts", type=Path, default=ROOT / "database" / "rvce_course_conflicts.json")
    args = parser.parse_args()
    manifest = json.loads((ROOT / "database" / "rvce_source_documents.json").read_text(encoding="utf-8"))
    records: list[dict[str, Any]] = []
    for item in manifest["documents"]:
        records.extend(extract_document(args.source_root, item, manifest["source_url"]))
    grouped: dict[tuple[str, int, int, str], list[dict[str, Any]]] = {}
    for row in records:
        key = (row["program_code"], row["scheme_year"], row["semester"], row["course_code"])
        grouped.setdefault(key, []).append(row)
    conflicts = [rows for rows in grouped.values() if len({row["title"].casefold() for row in rows}) > 1]
    conflict_records = [row for rows in conflicts for row in rows]
    conflicting_ids = {id(row) for rows in conflicts for row in rows}
    records = [row for row in records if id(row) not in conflicting_ids]
    records.sort(key=lambda row: (row["scheme_year"], row["program_code"], row["semester"], row["course_code"], row["source_page"]))
    conflict_records.sort(key=lambda row: (row["scheme_year"], row["program_code"], row["semester"], row["course_code"], row["source_page"]))
    args.output.write_text(json.dumps(records, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    args.conflicts.write_text(json.dumps(conflict_records, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Extracted {len(records)} review candidates; quarantined {len(conflict_records)} conflicting rows from {len(manifest['documents'])} PDFs")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
