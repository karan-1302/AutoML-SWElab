# lab8/backend/routers/train.py
# ─────────────────────────────────────────────────────────────
# Thin Router: AutoML Training
# Updated for Lab 8: injects database session via DAL.
# ─────────────────────────────────────────────────────────────

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from models.schemas  import TrainStartRequest, TrainStatusResponse
from utils.security  import get_current_user
from bll.train_bll   import validate_training_request, start_training, get_formatted_training_status
from dal.database    import get_db

router = APIRouter()


@router.post("/start", status_code=status.HTTP_202_ACCEPTED)
def start_training_endpoint(
    body: TrainStartRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Start AutoML training with DAL integration."""
    can_proceed, result = validate_training_request(
        dataset_id=body.dataset_id,
        target_column=body.target_column,
        user_id=current_user["user_id"],
        db=db,
    )

    if not can_proceed:
        raise HTTPException(
            status_code=result.get("code", 400),
            detail=result["errors"],
        )

    start_training(
        user_id=current_user["user_id"],
        df=result["df"],
        target_column=body.target_column,
        dataset_id=body.dataset_id,
        db=db,
    )

    return {"message": "AutoML training started.", "target_column": body.target_column}


@router.get("/status")
def get_training_status(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Poll for training progress."""
    return get_formatted_training_status(current_user["user_id"], db)
