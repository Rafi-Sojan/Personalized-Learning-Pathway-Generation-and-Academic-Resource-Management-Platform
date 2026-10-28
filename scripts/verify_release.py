"""Verify repository-owned release invariants without contacting external services."""

from __future__ import annotations

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
    "backend/migrations/versions/0006_processing_reliability.py",
)
REQUIRED_ENV = (
    "SECRET_KEY=",
    "POSTGRES_PASSWORD=",
    "DOCUMENT_MAX_PROCESSING_ATTEMPTS=",
    "DOCUMENT_RETRY_DELAY_SECONDS=",
    "METRICS_AUTH_TOKEN=",
)


def main() -> int:
    failures: list[str] = []
    for relative in REQUIRED_FILES:
        if not (ROOT / relative).is_file():
            failures.append(f"missing required release artifact: {relative}")

    env_text = (ROOT / ".env.example").read_text(encoding="utf-8")
    for key in REQUIRED_ENV:
        if key not in env_text:
            failures.append(f"missing configuration template entry: {key}")

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
    print(f"Release verification passed: {len(REQUIRED_FILES)} controlled artifacts and workflow pins checked.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
