# lab8/backend/dal/db_models.py
# ─────────────────────────────────────────────────────────────
# SQLAlchemy ORM models — the database schema for the Real Estate
# AutoML system.
#
# Tables:
#   users          — registered users with hashed passwords
#   datasets       — metadata for uploaded CSV datasets
#   training_jobs  — AutoML training run state & scores
#   predictions    — saved prediction results
# ─────────────────────────────────────────────────────────────

from datetime import datetime, timezone
from sqlalchemy import (
    Column, Integer, String, Float, Text, DateTime, ForeignKey, UniqueConstraint
)
from sqlalchemy.orm import relationship
from dal.database import Base


class User(Base):
    """Registered user of the AutoML platform."""
    __tablename__ = "users"

    id              = Column(Integer, primary_key=True, autoincrement=True)
    user_id         = Column(String(50), unique=True, nullable=False, index=True)
    email           = Column(String(255), unique=True, nullable=False, index=True)
    name            = Column(String(255), nullable=False)
    hashed_password = Column(String(255), nullable=False)
    created_at      = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    datasets      = relationship("Dataset", back_populates="owner", cascade="all, delete-orphan")
    training_jobs = relationship("TrainingJob", back_populates="owner", cascade="all, delete-orphan")
    predictions   = relationship("Prediction", back_populates="owner", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User(user_id='{self.user_id}', email='{self.email}')>"


class Dataset(Base):
    """Metadata for an uploaded CSV dataset."""
    __tablename__ = "datasets"

    id           = Column(Integer, primary_key=True, autoincrement=True)
    dataset_id   = Column(String(50), unique=True, nullable=False, index=True)
    filename     = Column(String(255), nullable=False)
    user_id      = Column(String(50), ForeignKey("users.user_id"), nullable=False)
    columns_json = Column(Text, nullable=False)       # JSON-serialized list of column names
    row_count    = Column(Integer, nullable=False)
    created_at   = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    owner = relationship("User", back_populates="datasets")

    def __repr__(self):
        return f"<Dataset(dataset_id='{self.dataset_id}', filename='{self.filename}')>"


class TrainingJob(Base):
    """State of an AutoML training run."""
    __tablename__ = "training_jobs"

    id                   = Column(Integer, primary_key=True, autoincrement=True)
    user_id              = Column(String(50), ForeignKey("users.user_id"), nullable=False)
    status               = Column(String(20), nullable=False, default="idle")  # idle|running|done|error
    progress_json        = Column(Text, default="{}")          # JSON dict of algo → pct
    scores_json          = Column(Text, default="{}")          # JSON dict of algo → metrics
    best_model_name      = Column(String(100), nullable=True)
    target_column        = Column(String(255), nullable=True)
    feature_columns_json = Column(Text, default="[]")          # JSON list
    error_message        = Column(Text, nullable=True)
    created_at           = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at           = Column(DateTime, default=lambda: datetime.now(timezone.utc),
                                  onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    owner = relationship("User", back_populates="training_jobs")

    def __repr__(self):
        return f"<TrainingJob(user_id='{self.user_id}', status='{self.status}')>"


class Prediction(Base):
    """A saved prediction result."""
    __tablename__ = "predictions"

    id                  = Column(Integer, primary_key=True, autoincrement=True)
    user_id             = Column(String(50), ForeignKey("users.user_id"), nullable=False)
    predicted_price     = Column(Float, nullable=False)
    model_used          = Column(String(100), nullable=False)
    confidence          = Column(Float, nullable=False)
    input_features_json = Column(Text, nullable=False)  # JSON dict of input features
    created_at          = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    owner = relationship("User", back_populates="predictions")

    def __repr__(self):
        return f"<Prediction(user_id='{self.user_id}', price={self.predicted_price})>"
