import sys
import os
import pytest

# add the backend folder to the path so imports like "from dal.database import ..."
# work when pytest runs from inside the tests/ directory
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

from dal.database import Base, get_db
from dal.db_models import User
from utils.security import create_access_token, hash_password
from main import app


@pytest.fixture(scope="function")
def test_db():
    # creates a fresh in-memory SQLite database for each test
    # using StaticPool so the same connection is reused within the test
    # everything is dropped at the end so tests don't bleed into each other
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)

    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def seeded_db(test_db):
    # builds on test_db by inserting one demo user
    # this is the user we log in as in most tests
    demo_user = User(
        user_id="user-001",
        email="demo@realestate.com",
        name="Demo Agent",
        hashed_password=hash_password("password123"),
    )
    test_db.add(demo_user)
    test_db.commit()
    test_db.refresh(demo_user)
    return test_db


@pytest.fixture(scope="function")
def client(seeded_db):
    # creates a FastAPI test client that uses our in-memory DB instead of the real one
    # we do this by overriding the get_db dependency that FastAPI injects into routes
    # after the test finishes, the override is cleared so it doesn't affect other tests
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
    # generates a real JWT for the demo user
    # useful when we need to pass a valid token in the Authorization header
    return create_access_token({
        "sub":   "user-001",
        "email": "demo@realestate.com",
        "name":  "Demo Agent",
    })


@pytest.fixture(scope="function")
def auth_headers(auth_token):
    # wraps the token in the header format FastAPI expects
    return {"Authorization": f"Bearer {auth_token}"}
