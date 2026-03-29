# lab7/backend/bll/train_bll.py
# ─────────────────────────────────────────────────────────────
# AutoML Training Business Logic Layer
#
# Business Rules Implemented:
#   BR-TRN-01  Dataset must exist in the store.
#   BR-TRN-02  Target column must exist in the dataset.
#   BR-TRN-03  Target column must be numeric (regression).
#   BR-TRN-04  Only one training job can run at a time per user.
#   BR-TRN-05  Dataset must have at least 20 rows for train/test split.
#   BR-TRN-06  Best model is selected by highest R² score.
#   BR-TRN-07  Model scores are rounded for readability.
#
# Data Transformation:
#   DT-TRN-01  Raw training job dict → TrainStatusResponse with formatted scores.
#   DT-TRN-02  Progress percentages normalised to 0-100 range.
# ─────────────────────────────────────────────────────────────

import threading
from typing import Tuple

import pandas as pd

from models.schemas        import TrainStatusResponse, ModelScore
from utils.store           import DATASETS, get_training_job
from services.automl_trainer import run_automl, ALGORITHMS


MIN_ROWS_FOR_TRAINING = 20


# ── Validation ────────────────────────────────────────────────

def validate_training_request(
    dataset_id: str,
    target_column: str,
    user_id: str,
) -> Tuple[bool, dict]:
    """
    Validate that training can proceed.

    Returns
    -------
    (can_proceed, payload)
        On success: (True, {"dataset": ..., "df": DataFrame})
        On failure: (False, {"errors": [...], "code": int})
    """
    errors: list[str] = []

    # BR-TRN-01: Dataset must exist
    dataset = DATASETS.get(dataset_id)
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
    existing = get_training_job(user_id)
    if existing and existing.get("status") == "running":
        return False, {
            "errors": ["A training job is already running. Please wait for it to complete."],
            "code": 409,
        }

    return True, {"dataset": dataset, "df": df.copy()}


# ── Launch training ───────────────────────────────────────────

def start_training(user_id: str, df: pd.DataFrame, target_column: str):
    """
    Launch AutoML training in a background thread.
    The actual ML logic lives in services/automl_trainer.py.
    """
    t = threading.Thread(
        target=run_automl,
        args=(user_id, df, target_column),
        daemon=True,
    )
    t.start()


# ── Status transformation (DT-TRN-01, DT-TRN-02) ────────────

def get_formatted_training_status(user_id: str) -> dict:
    """
    Transform the raw training job data into a presentation-ready format.
    
    Data Transformation:
      - Raw progress dict → filtered to only algorithm keys (strip _score keys)
      - Raw scores dict → list of ModelScore objects sorted by R²
      - Status string normalised to 'idle' | 'running' | 'done' | 'error'
    """
    job = get_training_job(user_id)

    if not job:
        return {
            "status":     "idle",
            "progress":   {algo: 0 for algo in ALGORITHMS},
            "complete":   False,
            "best_model": None,
            "all_models": None,
        }

    is_done = job["status"] == "done"

    # DT-TRN-01: Transform best model data
    best_model_out = None
    all_models_out = None

    if is_done and job.get("best_model_name"):
        name   = job["best_model_name"]
        scores = job["scores"][name]

        # BR-TRN-06: Best model by R²
        best_model_out = ModelScore(
            name=name,
            r2=round(scores["r2"], 6),       # BR-TRN-07
            rmse=round(scores["rmse"], 4),
            mae=round(scores["mae"], 4),
        )

        # All models for comparison table
        all_models_out = [
            ModelScore(name=n, r2=round(s["r2"], 6), rmse=round(s["rmse"], 4), mae=round(s["mae"], 4))
            for n, s in job.get("all_scores", job["scores"]).items()
        ]

    return {
        "status":     job["status"],
        "progress":   job.get("progress", {}),
        "complete":   is_done,
        "best_model": best_model_out,
        "all_models": all_models_out,
    }
