# lab8/backend/tests/conftest.py
# ─────────────────────────────────────────────────────────────
# Pytest fixtures for White Box and Black Box testing.
#
# Provides:
#   - In-memory SQLite test database (isolated per test)
#   - FastAPI TestClient with DB session override
#   - Pre-seeded demo user and auth token
# ─────────────────────────────────────────────────────────────

import sys
import os
import pytest

# Ensure the backend directory is on the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient
from passlib.context import CryptContext

from dal.database import Base, get_db
from dal.db_models import User, Dataset, TrainingJob, Prediction
from utils.security import create_access_token
from main import app

# ── Password context ──────────────────────────────────────────
_pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")


# ── Test Database ─────────────────────────────────────────────

from sqlalchemy.pool import StaticPool

@pytest.fixture(scope="function")
def test_db():
    """
    Create an in-memory SQLite database for each test.
    Yields a Session and tears down after the test.
    """
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    # Create all tables
    Base.metadata.create_all(bind=engine)

    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def seeded_db(test_db):
    """
    Test database pre-seeded with a demo user.
    """
    demo_user = User(
        user_id="user-001",
        email="demo@realestate.com",
        name="Demo Agent",
        hashed_password=_pwd.hash("password123"),
    )
    test_db.add(demo_user)
    test_db.commit()
    test_db.refresh(demo_user)
    return test_db


# ── FastAPI Test Client ───────────────────────────────────────

@pytest.fixture(scope="function")
def client(seeded_db):
    """
    FastAPI TestClient with the database session overridden
    to use the in-memory test database.
    """
    def _override_get_db():
        try:
            yield seeded_db
        finally:
            pass

    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def auth_token():
    """
    A valid JWT token for the demo user.
    Can be used in Authorization headers for protected endpoints.
    """
    return create_access_token({
        "sub":   "user-001",
        "email": "demo@realestate.com",
        "name":  "Demo Agent",
    })


@pytest.fixture(scope="function")
def auth_headers(auth_token):
    """Authorization headers with a valid Bearer token."""
    return {"Authorization": f"Bearer {auth_token}"}
