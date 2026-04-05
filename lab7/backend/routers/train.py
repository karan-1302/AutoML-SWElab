# lab7/backend/routers/train.py
# ─────────────────────────────────────────────────────────────
# Thin Router: AutoML Training
# Delegates all business logic to bll/train_bll.py
# ─────────────────────────────────────────────────────────────

from fastapi import APIRouter, Depends, HTTPException, status

from models.schemas  import TrainStartRequest, TrainStatusResponse
from utils.security  import get_current_user
from bll.train_bll   import validate_training_request, start_training, get_formatted_training_status

router = APIRouter()


@router.post("/start", status_code=status.HTTP_202_ACCEPTED)
def start_training_endpoint(
    body: TrainStartRequest,
    current_user: dict = Depends(get_current_user),
):
    """
    Start AutoML training.
    The router validates the request via BLL and launches
    training in a background thread.
    """
    # Delegate validation to BLL
    can_proceed, result = validate_training_request(
        dataset_id=body.dataset_id,
        target_column=body.target_column,
        user_id=current_user["user_id"],
    )

    if not can_proceed:
        raise HTTPException(
            status_code=result.get("code", 400),
            detail=result["errors"],
        )

    # Delegate training launch to BLL
    start_training(
        user_id=current_user["user_id"],
        df=result["df"],
        target_column=body.target_column,
    )

    return {"message": "AutoML training started.", "target_column": body.target_column}


@router.get("/status")
def get_training_status(current_user: dict = Depends(get_current_user)):
    """
    Poll for training progress.
    The BLL transforms the raw job data into a presentation-ready format.
    """
    return get_formatted_training_status(current_user["user_id"])
