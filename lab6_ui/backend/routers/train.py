# backend/routers/train.py
# UC-04: Initiate AutoML  |  UC-05: Select Target  |  UC-06-08: Train, Evaluate, Best Model
#
# POST /api/train/start   → validates dataset + target → kicks off background thread
# GET  /api/train/status  → returns live progress percentages + best model on completion

import threading

from fastapi import APIRouter, Depends, HTTPException, status

from models.schemas        import TrainStartRequest, TrainStatusResponse, ModelScore
from utils.security        import get_current_user
from utils.store           import DATASETS, get_training_job
from services.automl_trainer import run_automl, ALGORITHMS

router = APIRouter()


@router.post("/start", status_code=status.HTTP_202_ACCEPTED)
def start_training(
    body: TrainStartRequest,
    current_user: dict = Depends(get_current_user),
):
    """
    Validate the dataset and target column, then launch the AutoML
    training pipeline in a background daemon thread so the API stays
    non-blocking (mirrors the Render-hosted architecture described in
    Assignment 5).
    """
    # ── 1. Verify dataset exists and belongs to this user ─────
    dataset = DATASETS.get(body.dataset_id)
    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Dataset '{body.dataset_id}' not found. Please upload a dataset first.",
        )

    # ── 2. Verify target column exists ────────────────────────
    if body.target_column not in dataset["columns"]:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Column '{body.target_column}' not found in dataset. "
                   f"Available columns: {dataset['columns']}",
        )

    # ── 3. Check if training is already running ───────────────
    existing = get_training_job(current_user["user_id"])
    if existing and existing.get("status") == "running":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A training job is already running. Wait for it to complete.",
        )

    # ── 4. Launch background training thread ──────────────────
    df = dataset["dataframe"].copy()
    t  = threading.Thread(
        target=run_automl,
        args=(current_user["user_id"], df, body.target_column),
        daemon=True,
    )
    t.start()

    return {"message": "AutoML training started.", "target_column": body.target_column}


@router.get("/status", response_model=TrainStatusResponse)
def get_training_status(current_user: dict = Depends(get_current_user)):
    """
    Poll this endpoint every 2 seconds from the frontend to get live
    per-algorithm progress percentages and the best model on completion.
    """
    job = get_training_job(current_user["user_id"])
    if not job:
        return TrainStatusResponse(
            status="idle",
            progress={algo: 0 for algo in ALGORITHMS},
            complete=False,
        )

    is_done = job["status"] == "done"

    best_model_out = None
    all_models_out = None

    if is_done and job.get("best_model_name"):
        name   = job["best_model_name"]
        scores = job["scores"][name]
        best_model_out = ModelScore(
            name=name,
            r2=scores["r2"],
            rmse=scores["rmse"],
            mae=scores["mae"],
        )

        # All model comparison
        all_models_out = [
            ModelScore(name=n, **s)
            for n, s in job.get("all_scores", job["scores"]).items()
        ]

    return TrainStatusResponse(
        status=job["status"],
        progress=job.get("progress", {}),
        complete=is_done,
        best_model=best_model_out,
        all_models=all_models_out,
    )
