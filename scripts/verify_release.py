"""Verify repository-owned release invariants without contacting external services."""

from __future__ import annotations

import ast
import re
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
    "backend/app/api/v1/progress.py",
    "frontend/src/pages/RvceCatalog.tsx",
    "frontend/src/pages/Dashboard.tsx",
    "frontend/src/pages/Progress.tsx",
    "frontend/src/utils/activity.ts",
    "frontend/src/App.tsx",
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
TS_FUNCTION_DECLARATION = re.compile(r"^\s*(?:export\s+)?(?:default\s+)?(?:async\s+)?function\s+([A-Za-z_$][\w$]*)")
TS_FUNCTION_VARIABLE = re.compile(r"^\s*(?:export\s+)?(?:const|let)\s+([A-Za-z_$][\w$]*)\s*(?::[^=]+)?=\s*(.*)$")
CPP_METHOD_DECLARATION = re.compile(r"^\s*(?:Score|std::vector<Score>)\s+\w+\s*\([^;]*\)\s*const;\s*$")


def verify_frontend_function_comments() -> tuple[int, list[str]]:
    """Require leading JSDoc for named frontend functions and callable variables."""
    count = 0
    failures: list[str] = []
    for source_file in (ROOT / "frontend" / "src").rglob("*.ts*"):
        if source_file.suffix not in {".ts", ".tsx"}:
            continue
        lines = source_file.read_text(encoding="utf-8").splitlines()
        for index, line in enumerate(lines):
            declaration = TS_FUNCTION_DECLARATION.match(line)
            if declaration is None:
                declaration = TS_FUNCTION_VARIABLE.match(line)
                if declaration is None:
                    continue
                initializer_lines = [declaration.group(2)]
                for following in lines[index + 1 : index + 6]:
                    if re.match(r"^\s*(?:const|let|return)\b", following):
                        break
                    initializer_lines.append(following)
                    if ";" in following:
                        break
                initializer = "\n".join(initializer_lines)
                initializer_head = initializer.lstrip()
                direct_callable = re.match(r"(?:async\s*)?\([^)]*\)\s*(?::[^=]+)?\s*=>", initializer_head, re.DOTALL)
                callback_factory = re.match(r"useCallback\(\s*(?:async\s*)?\([^)]*\)\s*=>", initializer_head, re.DOTALL)
                if not (direct_callable or callback_factory):
                    continue
            count += 1
            previous = index - 1
            while previous >= 0 and not lines[previous].strip():
                previous -= 1
            comment = lines[previous].strip() if previous >= 0 else ""
            if not (comment.startswith("/**") or comment.startswith("*") or comment.startswith("//")):
                relative = source_file.relative_to(ROOT).as_posix()
                failures.append(f"missing function JSDoc: {relative}:{index + 1}:{declaration.group(1)}")
    return count, failures


def verify_cpp_api_comments() -> tuple[int, list[str]]:
    """Require Doxygen comments on public scorer declarations and comments on entry points."""
    count = 0
    failures: list[str] = []
    header = ROOT / "scoring-engine" / "include" / "scoring" / "scorer.hpp"
    lines = header.read_text(encoding="utf-8").splitlines()
    for index, line in enumerate(lines):
        if CPP_METHOD_DECLARATION.match(line):
            count += 1
            previous = lines[index - 1].strip() if index else ""
            if not (previous.startswith("///") or previous.startswith("/**") or previous.endswith("*/")):
                failures.append(f"missing C++ API comment: {header.relative_to(ROOT).as_posix()}:{index + 1}")

    entry_point = re.compile(r"^\s*int\s+main\s*\(")
    for source_file in (ROOT / "scoring-engine").rglob("*.cpp"):
        lines = source_file.read_text(encoding="utf-8").splitlines()
        for index, line in enumerate(lines):
            if entry_point.match(line):
                previous = index - 1
                while previous >= 0 and not lines[previous].strip():
                    previous -= 1
                comment = lines[previous].strip() if previous >= 0 else ""
                if not (comment.startswith("//") or comment.startswith("/*") or comment.endswith("*/")):
                    failures.append(f"missing C++ entry-point comment: {source_file.relative_to(ROOT).as_posix()}:{index + 1}")
    return count, failures


def main() -> int:
    """Check release artifacts, configuration, workflow pins, and function comments across languages."""
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

    frontend_function_count, frontend_failures = verify_frontend_function_comments()
    cpp_method_count, cpp_failures = verify_cpp_api_comments()
    failures.extend(frontend_failures)
    failures.extend(cpp_failures)

    if failures:
        print("Release verification failed:")
        print("\n".join(f"- {failure}" for failure in failures))
        return 1
    print(
        f"Release verification passed: {len(REQUIRED_FILES)} controlled artifacts, "
        f"{documented_function_count} Python docstrings, {frontend_function_count} frontend function comments, "
        f"{cpp_method_count} C++ API comments, and workflow pins checked."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
