"""Shared isolation for process-local API instrumentation and throttling in tests."""

import pytest


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
