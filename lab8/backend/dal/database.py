# lab8/backend/dal/database.py
# ─────────────────────────────────────────────────────────────
# SQLAlchemy engine, session factory, and Base declarative class.
#
# Uses SQLite for this assignment (file: automl.db).
# In production, swap the DATABASE_URL for PostgreSQL / Supabase.
# ─────────────────────────────────────────────────────────────

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# ── Database URL ──────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    f"sqlite:///{os.path.join(BASE_DIR, 'automl.db')}"
)

# ── Engine ────────────────────────────────────────────────────
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},  # SQLite-specific
    echo=False,
)

# ── Session factory ───────────────────────────────────────────
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# ── Declarative Base ──────────────────────────────────────────
Base = declarative_base()


def init_db():
    """Create all tables defined by SQLAlchemy models."""
    from dal.db_models import User, Dataset, TrainingJob, Prediction  # noqa: F401
    Base.metadata.create_all(bind=engine)


def get_db():
    """FastAPI dependency — yields a DB session and closes it after the request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
