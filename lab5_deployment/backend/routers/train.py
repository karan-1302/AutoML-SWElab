# backend/routers/train.py
# Layer 2: AutoML Training router
# POST /api/train/start   →  BLL AutoMLTrainer.trainAll()  (background thread)
# GET  /api/train/status  →  returns live progress from D3 store
# Maps to UC-05/06/07/08  (Lab 4 Section V)

import threading
import pandas as pd
from fastapi import APIRouter, Depends, HTTPException, status

from models.schemas  import TrainStartRequest, TrainStatusResponse, ModelScore
from utils.security  import get_current_user
from utils.store     import get_dataset, get_training_job
from services.automl_trainer import run_automl

router = APIRouter()


@router.post("/start")
def start_training(
    body: TrainStartRequest,
    current_user: dict = Depends(get_current_user),
):
    """
    Kick off AutoML training in a background thread.

    Layer flow (Lab 4 Section II — "Complete Example: Training a Model"):
      Layer 2 receives config
      → BLL AutoMLTrainer.trainAll() runs in background
      → BLL evaluates models, picks best
      → DAL saves pipeline to D3 (Model Registry)
    """
    dataset = get_dataset(body.dataset_id)
    if not dataset:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Dataset not found. Upload a CSV first.")

    df: pd.DataFrame = dataset["dataframe"]

    if body.target_column not in df.columns:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Column '{body.target_column}' not found in dataset.",
        )

    # Start BLL AutoMLTrainer in a daemon thread so the HTTP response returns immediately
    thread = threading.Thread(
        target=run_automl,
        args=(current_user["user_id"], df, body.target_column),
        daemon=True,
    )
    thread.start()

    return {
        "message":       "AutoML training started.",
        "dataset_id":    body.dataset_id,
        "target_column": body.target_column,
        "poll_url":      "/api/train/status",
    }


@router.get("/status", response_model=TrainStatusResponse)
def training_status(current_user: dict = Depends(get_current_user)):
    """
    Poll training progress.  Frontend calls this every 2 s to update the progress bar.
    """
    job = get_training_job(current_user["user_id"])
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="No training job found. Start training first.")

    complete   = job["status"] == "done"
    best_model = None
    all_models = None

    if complete:
        best_name  = job["best_model_name"]
        all_scores = job.get("all_scores", {})

        best_model = ModelScore(
            name=best_name,
            **all_scores[best_name],
        )
        all_models = [
            ModelScore(name=name, **scores)
            for name, scores in all_scores.items()
        ]

    return TrainStatusResponse(
        status=job["status"],
        progress=job.get("progress", {}),
        complete=complete,
        best_model=best_model,
        all_models=all_models,
    )
