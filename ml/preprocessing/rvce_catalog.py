"""Load and validate the source-controlled RVCE catalog manifest."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


DEFAULT_CATALOG_PATH = Path(__file__).resolve().parents[1].parent / "database" / "rvce_catalog.json"


def load_rvce_catalog(path: Path = DEFAULT_CATALOG_PATH) -> dict[str, Any]:
    catalog = json.loads(path.read_text(encoding="utf-8"))
    validate_rvce_catalog(catalog)
    return catalog


def validate_rvce_catalog(catalog: dict[str, Any]) -> None:
    institution = catalog.get("institution", {})
    if institution.get("short_name") != "RVCE" or not institution.get("source_url"):
        raise ValueError("RVCE catalog must include institution identity and source provenance")
    programs = catalog.get("program_schemes", [])
    codes = [program.get("code") for program in programs]
    if len(codes) != len(set(codes)) or any(not code for code in codes):
        raise ValueError("RVCE program codes must be present and unique")
    for program in programs:
        if not program.get("name") or not program.get("schemes"):
            raise ValueError(f"RVCE program metadata is incomplete: {program!r}")
    for document in catalog.get("document_matrix", []):
        if not document.get("source_url") or not document.get("semesters"):
            raise ValueError(f"RVCE document source metadata is incomplete: {document!r}")
