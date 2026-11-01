"""Verify repository-owned release invariants without contacting external services."""

from __future__ import annotations

import ast
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REQUIRED_FILES = (
    "README.md",
    ".env.example",
    "docker-compose.yaml",
    "docs/document-control.md",
    "docs/requirements-traceability.md",
    "docs/deployment-and-release.md",
    "docs/operational-readiness.md",
    "docs/privacy-impact-assessment.md",
    "docs/service-level-objectives.md",
    "docs/accessibility-and-performance.md",
    "docs/security-acceptance.md",
    "docs/security-audit.md",
    "docs/release-acceptance.md",
    "docs/rvce-catalog.md",
    "monitoring/prometheus.yml",
    "monitoring/alert-rules.yml",
    "monitoring/README.md",
    "database/rvce_catalog.json",
    "database/rvce_source_documents.json",
    "database/rvce-course-record.schema.json",
    "database/rvce_courses.json",
    "database/rvce_course_candidates.json",
    "database/rvce_course_conflicts.json",
    "backend/app/api/v1/catalog.py",
    "backend/app/schemas/rvce.py",
    "frontend/src/pages/RvceCatalog.tsx",
    "frontend/src/pages/Admin.tsx",
    "frontend/src/services/rvce.ts",
    "scripts/extract_rvce_candidates.py",
    "scripts/import_rvce_candidates.py",
    "scripts/validate_rvce_courses.py",
    "docs/implementation-record.md",
    "docs/remaining-targets.md",
    "backend/tests/test_rvce_catalog.py",
    "backend/requirements.txt",
    "backend/requirements-ocr.txt",
    "backend/requirements-storage.txt",
    "ml/requirements.txt",
    "frontend/package-lock.json",
    ".github/workflows/release-gates.yml",
    "docs/code-commenting-standard.md",
    "database/init.sql",
    "backend/migrations/versions/0006_processing_reliability.py",
    "backend/migrations/versions/0007_rvce_syllabus_courses.py",
    "backend/migrations/versions/0008_rvce_source_page.py",
)
REQUIRED_ENV = (
    "SECRET_KEY=",
    "POSTGRES_PASSWORD=",
    "DOCUMENT_MAX_PROCESSING_ATTEMPTS=",
    "DOCUMENT_RETRY_DELAY_SECONDS=",
    "METRICS_AUTH_TOKEN=",
)
DOCUMENTED_PYTHON_ROOTS = ("backend", "ml", "scripts", "tests")


def main() -> int:
    """Check required release artifacts, configuration keys, migration startup, and pinned actions."""
    failures: list[str] = []
    for relative in REQUIRED_FILES:
        if not (ROOT / relative).is_file():
            failures.append(f"missing required release artifact: {relative}")

    env_text = (ROOT / ".env.example").read_text(encoding="utf-8")
    for key in REQUIRED_ENV:
        if key not in env_text:
            failures.append(f"missing configuration template entry: {key}")

    documented_function_count = 0
    documented_source_files = [ROOT / "conftest.py"]
    for relative_root in DOCUMENTED_PYTHON_ROOTS:
        documented_source_files.extend((ROOT / relative_root).rglob("*.py"))
    for source_file in documented_source_files:
        relative = source_file.relative_to(ROOT).as_posix()
        module = ast.parse(source_file.read_text(encoding="utf-8"), filename=relative)
        for node in ast.walk(module):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                documented_function_count += 1
                if ast.get_docstring(node) is None:
                    failures.append(f"missing function docstring: {relative}:{node.lineno}:{node.name}")

    compose_text = (ROOT / "docker-compose.yaml").read_text(encoding="utf-8")
    if "alembic upgrade head" not in compose_text:
        failures.append("Compose backend does not apply migrations before startup")

    workflow_root = ROOT / ".github" / "workflows"
    action_pattern = re.compile(r"^\s*(?:-\s*)?uses:\s+[^\s@]+@([0-9a-f]{40})(?:\s+#.*)?$")
    for workflow in workflow_root.glob("*.yml"):
        for line_number, line in enumerate(workflow.read_text(encoding="utf-8").splitlines(), start=1):
            if "uses:" in line and not action_pattern.match(line):
                failures.append(f"un-pinned workflow action: {workflow.relative_to(ROOT)}:{line_number}")

    if failures:
        print("Release verification failed:")
        print("\n".join(f"- {failure}" for failure in failures))
        return 1
    print(f"Release verification passed: {len(REQUIRED_FILES)} controlled artifacts, {documented_function_count} Python function docstrings, and workflow pins checked.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
