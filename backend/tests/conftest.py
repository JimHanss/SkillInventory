import os

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session

from skill_inventory.db import get_session
from skill_inventory.main import create_app


@pytest.fixture(scope="session")
def engine():
    url = os.getenv("TEST_DATABASE_URL")
    if not url:
        pytest.skip("TEST_DATABASE_URL required for real PostgreSQL integration tests")
    parsed = make_url(url)
    if not parsed.database or not parsed.database.endswith("_test"):
        raise RuntimeError("Test database name must end with _test; refusing to modify it")
    previous = os.environ.get("DATABASE_URL")
    os.environ["DATABASE_URL"] = url
    try:
        command.upgrade(Config("alembic.ini"), "head")
    finally:
        if previous is None:
            os.environ.pop("DATABASE_URL", None)
        else:
            os.environ["DATABASE_URL"] = previous
    value = create_engine(url, pool_pre_ping=True)
    yield value
    value.dispose()


@pytest.fixture
def client(engine):
    with engine.begin() as connection:
        connection.execute(text("TRUNCATE published_skills, skills CASCADE"))

    def session_override():
        with Session(engine) as session:
            yield session

    app = create_app(health_check=lambda: None)
    app.dependency_overrides[get_session] = session_override
    with TestClient(app, base_url="http://localhost") as value:
        yield value


@pytest.fixture
def draft():
    return {
        "slug": "code-review",
        "name": "代码审查",
        "description": "Review safely",
        "content": "# Review\n检查代码。😀\n",
    }
