import os

import pytest
from redis import Redis
from sqlalchemy import create_engine, text


pytestmark = pytest.mark.integration


def test_postgres_and_redis_connectivity() -> None:
    if os.getenv("INTEGRATION_TESTS") != "1":
        pytest.skip("Set INTEGRATION_TESTS=1 to run service integration checks")
    database_url = os.environ["DATABASE_URL"]
    redis_url = os.environ["REDIS_URL"]
    engine = create_engine(database_url, pool_pre_ping=True)
    with engine.connect() as connection:
        assert connection.execute(text("SELECT 1")).scalar_one() == 1
    assert Redis.from_url(redis_url).ping() is True
