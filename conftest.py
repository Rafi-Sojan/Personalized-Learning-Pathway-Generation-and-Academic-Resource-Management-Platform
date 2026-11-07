"""Shared filesystem, database, instrumentation, and throttling isolation for tests."""

import os
import shutil
import tempfile
from pathlib import Path

import pytest


_TEST_RUNTIME_DIR = Path(tempfile.mkdtemp(prefix="learning-roadmap-tests-"))
_TEST_DATABASE_URL = f"sqlite:///{(_TEST_RUNTIME_DIR / 'learning.db').as_posix()}"
os.environ["ENVIRONMENT"] = "test"
if os.getenv("INTEGRATION_TESTS") != "1":
    os.environ["DATABASE_URL"] = _TEST_DATABASE_URL
    os.environ["UPLOAD_DIR"] = str(_TEST_RUNTIME_DIR / "uploads")
    os.environ["PROCESSED_DIR"] = str(_TEST_RUNTIME_DIR / "processed")


@pytest.fixture(scope="session", autouse=True)
def isolated_test_runtime():
    """Dispose the test engine and remove only the temporary runtime created here."""
    yield
    from app.db.session import engine

    engine.dispose()
    shutil.rmtree(_TEST_RUNTIME_DIR, ignore_errors=True)


@pytest.fixture(autouse=True)
def reset_process_local_test_state():
    """Reset in-memory metrics and rate-limit windows between independent tests."""
    from app.core.metrics import metrics
    from app.infrastructure.rate_limiter import expensive_limiter, login_limiter

    metrics.requests.clear()
    metrics.statuses.clear()
    metrics.worker.clear()
    login_limiter._requests.clear()
    expensive_limiter._requests.clear()
