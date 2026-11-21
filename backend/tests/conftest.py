import os
import shutil

os.environ["DATABASE_URL"] = "postgresql+psycopg://secondbrain:devpassword@localhost:5432/secondbrain_test"
os.environ["JWT_SECRET"] = "test-secret"
os.environ["OPENAI_API_KEY"] = "test-openai-key"
os.environ["ANTHROPIC_API_KEY"] = "test-anthropic-key"
os.environ["UPLOAD_DIR"] = "test_uploads"

import pytest # noqa: E402
from fastapi.testclient import TestClient # noqa: E402
from sqlalchemy import text # noqa: E402
from app import models # noqa: E402, F401
from app.config import settings # noqa: E402
from app.db import Base, engine # noqa: E402
from app.main import app # noqa: E402

assert settings.database_url.endswith("_test"), "Refusing to run tests against a non-test database"

@pytest.fixture(scope="session", autouse=True)
def setup_database():
    with engine.begin() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    yield
    Base.metadata.drop_all(engine)
    shutil.rmtree(settings.upload_dir, ignore_errors=True)

@pytest.fixture(autouse=True)
def clean_tables():
    yield
    table_names = ", ".join(table.name for table in Base.metadata.sorted_tables)
    with engine.begin() as conn:
        conn.execute(text(f"TRUNCATE {table_names} RESTART IDENTITY CASCADE"))

@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client

@pytest.fixture
def make_user(client):
    def _make_user(email: str= "user@example.com", password : str = "password123") -> dict:
        client.post("/auth/signup", json={"email": email, "password" : password})
        res = client.post("/auth/login", json={"email": email, "password" : password})
        return {"Authorization" : f"Bearer {res.json()['access_token']}"}

    return _make_user

