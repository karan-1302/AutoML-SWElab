# lab8/backend/dal/seed.py
# ─────────────────────────────────────────────────────────────
# Database Seeding Script
#
# Seeds the database with a demo user for development and testing.
# Called on application startup; idempotent (skips if user exists).
# ─────────────────────────────────────────────────────────────

from passlib.context import CryptContext
from sqlalchemy.orm import Session

from dal.db_models import User
from dal.repositories.user_repository import get_user_by_email, create_user

_pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")

# ── Demo user credentials ─────────────────────────────────────
DEMO_USER = {
    "user_id":  "user-001",
    "email":    "demo@realestate.com",
    "name":     "Demo Agent",
    "password": "password123",
}


def seed_database(db: Session) -> None:
    """
    Seed the database with initial data.

    Currently seeds:
      - One demo user (demo@realestate.com / password123)

    This function is idempotent — running it multiple times
    will not create duplicate records.
    """
    # ── Seed demo user ────────────────────────────────────────
    existing = get_user_by_email(db, DEMO_USER["email"])
    if existing is None:
        create_user(
            db=db,
            user_id=DEMO_USER["user_id"],
            email=DEMO_USER["email"],
            name=DEMO_USER["name"],
            hashed_password=_pwd.hash(DEMO_USER["password"]),
        )
        print(f"[seed] Created demo user: {DEMO_USER['email']}")
    else:
        print(f"[seed] Demo user already exists: {DEMO_USER['email']}")
