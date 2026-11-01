"""Validate source-backed RVCE course rows before database import."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ml.preprocessing.rvce_catalog import load_rvce_catalog  # noqa: E402


REQUIRED = {"program_code", "scheme_year", "semester", "course_code", "title", "credits", "source_url", "source_checksum", "source_filename", "source_page", "verification_status"}


def validate_rows(rows: list[dict[str, Any]]) -> list[str]:
    """Check identity, catalog scope, status, and page-level source provenance for rows."""
    catalog = load_rvce_catalog()
    programs = {program["code"]: set(program["schemes"]) for program in catalog["program_schemes"]}
    aliases = {alias: program["code"] for program in catalog["program_schemes"] for alias in program.get("aliases", [])}
    common_schemes = set(catalog["common_first_year_schemes"])
    source_manifest_path = ROOT / "database" / "rvce_source_documents.json"
    source_manifest = json.loads(source_manifest_path.read_text(encoding="utf-8"))
    sources = {item["relative_path"]: item for item in source_manifest["documents"]}
    errors: list[str] = []
    seen: set[tuple[str, int, int, str]] = set()
    for index, row in enumerate(rows, start=1):
        missing = REQUIRED - row.keys()
        if missing:
            errors.append(f"row {index}: missing fields {sorted(missing)}")
            continue
        program_code = str(row["program_code"]).upper()
        normalized_code = aliases.get(program_code, program_code)
        scheme_year = row["scheme_year"]
        semester = row["semester"]
        if normalized_code == "BE-UNMAPPED":
            if semester not in (1, 2):
                errors.append(f"row {index}: BE-UNMAPPED records are limited to semesters 1 and 2")
            if scheme_year not in common_schemes:
                errors.append(f"row {index}: unsupported common first-year scheme {scheme_year}")
        elif normalized_code not in programs:
            errors.append(f"row {index}: unknown RVCE program code {program_code}")
        elif semester in (1, 2):
            if scheme_year not in common_schemes:
                errors.append(f"row {index}: unsupported common first-year scheme {scheme_year}")
        elif scheme_year not in programs.get(normalized_code, set()):
            errors.append(f"row {index}: scheme {scheme_year} is not catalogued for {normalized_code}")
        if not isinstance(semester, int) or not 1 <= semester <= 8:
            errors.append(f"row {index}: semester must be between 1 and 8")
        if not isinstance(row["credits"], (int, float)) or row["credits"] <= 0:
            errors.append(f"row {index}: credits must be positive")
        if row["verification_status"] not in {"pending_review", "academic_verified", "rejected"}:
            errors.append(f"row {index}: invalid verification_status")
        if len(str(row["source_checksum"])) != 64:
            errors.append(f"row {index}: source_checksum must be SHA-256")
        source = sources.get(str(row["source_filename"]))
        if source is None:
            errors.append(f"row {index}: source_filename is not in the inventoried RVCE document set")
        elif source["sha256"].lower() != str(row["source_checksum"]).lower():
            errors.append(f"row {index}: source_checksum does not match the inventoried PDF")
        if not isinstance(row["source_page"], int) or row["source_page"] < 1 or (source and row["source_page"] > source["pages"]):
            errors.append(f"row {index}: source_page must identify a page in the inventoried PDF")
        if row["source_url"] != source_manifest["source_url"]:
            errors.append(f"row {index}: source_url must match the official RVCE syllabus index")
        if not str(row["course_code"]).strip() or not str(row["title"]).strip():
            errors.append(f"row {index}: course_code and title must not be empty")
        identity = (normalized_code, int(scheme_year), int(semester), str(row["course_code"]).upper())
        if identity in seen:
            errors.append(f"row {index}: duplicate course identity {identity}")
        seen.add(identity)
    return errors


def main() -> int:
    """Validate a candidate JSON file and return a process status suitable for CI."""
    parser = argparse.ArgumentParser()
    parser.add_argument("records", type=Path, help="JSON array of source-backed RVCE course records")
    args = parser.parse_args()
    rows = json.loads(args.records.read_text(encoding="utf-8"))
    if not isinstance(rows, list):
        raise SystemExit("Course records must be a JSON array")
    errors = validate_rows(rows)
    if errors:
        print("RVCE course validation failed:")
        print("\n".join(f"- {error}" for error in errors))
        return 1
    print(f"RVCE course validation passed: {len(rows)} source-backed records.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
