# lab8/backend/dal/repositories/training_job_repository.py
# ─────────────────────────────────────────────────────────────
# Data Access Layer — Training Job Repository
#
# Provides CRUD operations for the `training_jobs` table.
# Stores training metadata and scores in SQLite; the actual
# sklearn Pipeline object remains in the in-memory runtime cache.
# ─────────────────────────────────────────────────────────────

import json
from typing import Optional
from sqlalchemy.orm import Session

from dal.db_models import TrainingJob


def create_or_update_job(
    db: Session,
    user_id: str,
    status: str = "idle",
    progress: dict = None,
    scores: dict = None,
    best_model_name: str = None,
    target_column: str = None,
    feature_columns: list = None,
    error_message: str = None,
) -> TrainingJob:
    """
    Create a new training job or update the existing one for a user.

    Each user has at most one active training job record.
    """
    job = db.query(TrainingJob).filter(TrainingJob.user_id == user_id).first()

    if job is None:
        job = TrainingJob(user_id=user_id)
        db.add(job)

    job.status               = status
    job.progress_json        = json.dumps(progress or {})
    job.scores_json          = json.dumps(scores or {})
    job.best_model_name      = best_model_name
    job.target_column        = target_column
    job.feature_columns_json = json.dumps(feature_columns or [])
    job.error_message        = error_message

    db.commit()
    db.refresh(job)
    return job


def get_job_by_user(db: Session, user_id: str) -> Optional[TrainingJob]:
    """Retrieve the latest training job for a user."""
    return db.query(TrainingJob).filter(TrainingJob.user_id == user_id).first()


def update_job_status(
    db: Session,
    user_id: str,
    status: str,
    progress: dict = None,
    scores: dict = None,
    best_model_name: str = None,
    feature_columns: list = None,
    error_message: str = None,
) -> Optional[TrainingJob]:
    """
    Partially update a training job's status and related fields.

    Returns the updated job, or None if not found.
    """
    job = db.query(TrainingJob).filter(TrainingJob.user_id == user_id).first()
    if job is None:
        return None

    job.status = status
    if progress is not None:
        job.progress_json = json.dumps(progress)
    if scores is not None:
        job.scores_json = json.dumps(scores)
    if best_model_name is not None:
        job.best_model_name = best_model_name
    if feature_columns is not None:
        job.feature_columns_json = json.dumps(feature_columns)
    if error_message is not None:
        job.error_message = error_message

    db.commit()
    db.refresh(job)
    return job


def delete_job(db: Session, user_id: str) -> bool:
    """Delete the training job for a user. Returns True if deleted."""
    job = db.query(TrainingJob).filter(TrainingJob.user_id == user_id).first()
    if job:
        db.delete(job)
        db.commit()
        return True
    return False


# ── Helpers to deserialise JSON fields ────────────────────────

def get_progress(job: TrainingJob) -> dict:
    """Deserialise progress_json to a Python dict."""
    return json.loads(job.progress_json) if job.progress_json else {}


def get_scores(job: TrainingJob) -> dict:
    """Deserialise scores_json to a Python dict."""
    return json.loads(job.scores_json) if job.scores_json else {}


def get_feature_columns(job: TrainingJob) -> list:
    """Deserialise feature_columns_json to a Python list."""
    return json.loads(job.feature_columns_json) if job.feature_columns_json else []
