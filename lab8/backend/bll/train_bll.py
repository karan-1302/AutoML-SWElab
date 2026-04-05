# lab8/backend/bll/train_bll.py
# ─────────────────────────────────────────────────────────────
# AutoML Training Business Logic Layer
#
# Updated for Lab 8: stores training metadata in the database
# (DAL) and keeps the Pipeline in the in-memory runtime cache.
#
# Business Rules Implemented:
#   BR-TRN-01  Dataset must exist in the cache.
#   BR-TRN-02  Target column must exist in the dataset.
#   BR-TRN-03  Target column must be numeric (regression).
#   BR-TRN-04  Only one training job can run at a time per user.
#   BR-TRN-05  Dataset must have at least 20 rows for train/test split.
#   BR-TRN-06  Best model is selected by highest R² score.
#   BR-TRN-07  Model scores are rounded for readability.
# ─────────────────────────────────────────────────────────────

import threading
from typing import Tuple

import pandas as pd
from sqlalchemy.orm import Session

from models.schemas import TrainStatusResponse, ModelScore
from dal.repositories.training_job_repository import (
    create_or_update_job, get_job_by_user, get_progress, get_scores
)
from utils.store import get_cached_dataset, get_cached_training
from services.automl_trainer import run_automl, ALGORITHMS


MIN_ROWS_FOR_TRAINING = 20


# ── Validation ────────────────────────────────────────────────

def validate_training_request(
    dataset_id: str,
    target_column: str,
    user_id: str,
    db: Session,
) -> Tuple[bool, dict]:
    """
    Validate that training can proceed.

    Returns
    -------
    (can_proceed, payload)
        On success: (True, {"df": DataFrame})
        On failure: (False, {"errors": [...], "code": int})
    """
    errors: list[str] = []

    # BR-TRN-01: Dataset must exist in cache
    dataset = get_cached_dataset(dataset_id)
    if not dataset:
        return False, {
            "errors": [f"Dataset '{dataset_id}' not found. Please upload a dataset first."],
            "code": 404,
        }

    # BR-TRN-02: Target column must exist
    if target_column not in dataset["columns"]:
        return False, {
            "errors": [
                f"Column '{target_column}' not found in dataset. "
                f"Available columns: {dataset['columns']}"
            ],
            "code": 422,
        }

    # BR-TRN-03: Target column must be numeric
    df = dataset["dataframe"]
    if not pd.api.types.is_numeric_dtype(df[target_column]):
        return False, {
            "errors": [
                f"Target column '{target_column}' must be numeric for regression. "
                f"Detected type: {df[target_column].dtype}"
            ],
            "code": 422,
        }

    # BR-TRN-05: Minimum rows
    valid_rows = df.dropna(subset=[target_column]).shape[0]
    if valid_rows < MIN_ROWS_FOR_TRAINING:
        return False, {
            "errors": [
                f"Dataset has only {valid_rows} valid rows (after removing NaN targets). "
                f"At least {MIN_ROWS_FOR_TRAINING} rows are required."
            ],
            "code": 422,
        }

    # BR-TRN-04: No concurrent training
    job = get_job_by_user(db, user_id)
    if job and job.status == "running":
        return False, {
            "errors": ["A training job is already running. Please wait for it to complete."],
            "code": 409,
        }

    return True, {"df": df.copy()}


# ── Launch training ───────────────────────────────────────────

def start_training(user_id: str, df: pd.DataFrame, target_column: str, db: Session):
    """
    Launch AutoML training in a background thread.
    Creates the initial job record in the database via DAL.
    """
    # Create initial job record in database
    create_or_update_job(
        db=db,
        user_id=user_id,
        status="running",
        progress={algo: 0 for algo in ALGORITHMS},
        scores={},
        target_column=target_column,
        feature_columns=[],
    )

    t = threading.Thread(
        target=run_automl,
        args=(user_id, df, target_column),
        daemon=True,
    )
    t.start()


# ── Status transformation ────────────────────────────────────

def get_formatted_training_status(user_id: str, db: Session) -> dict:
    """
    Transform the raw training job data into a presentation-ready format.
    Merges database metadata with runtime cache data.
    """
    # Check runtime cache first (has the most up-to-date progress)
    cached = get_cached_training(user_id)

    if cached:
        # Use cache for real-time progress data
        job_status = cached.get("status", "idle")
        progress = cached.get("progress", {})
        scores = cached.get("scores", {})
        best_name = cached.get("best_model_name")
        all_scores = cached.get("all_scores", scores)
    else:
        # Fallback to database
        job = get_job_by_user(db, user_id)
        if not job:
            return {
                "status":     "idle",
                "progress":   {algo: 0 for algo in ALGORITHMS},
                "complete":   False,
                "best_model": None,
                "all_models": None,
            }
        job_status = job.status
        progress = get_progress(job)
        scores = get_scores(job)
        best_name = job.best_model_name
        all_scores = scores

    is_done = job_status == "done"

    best_model_out = None
    all_models_out = None

    if is_done and best_name and best_name in scores:
        s = scores[best_name]
        best_model_out = ModelScore(
            name=best_name,
            r2=round(s["r2"], 6),
            rmse=round(s["rmse"], 4),
            mae=round(s["mae"], 4),
        )
        all_models_out = [
            ModelScore(name=n, r2=round(s2["r2"], 6), rmse=round(s2["rmse"], 4), mae=round(s2["mae"], 4))
            for n, s2 in all_scores.items()
        ]

    return {
        "status":     job_status,
        "progress":   progress,
        "complete":   is_done,
        "best_model": best_model_out,
        "all_models": all_models_out,
    }
