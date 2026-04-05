# lab8/backend/routers/predict.py
# ─────────────────────────────────────────────────────────────
# Thin Router: Prediction
# Updated for Lab 8: injects database session via DAL.
# ─────────────────────────────────────────────────────────────

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from models.schemas   import PredictRequest, PredictResponse
from utils.security   import get_current_user
from bll.predict_bll  import validate_and_predict
from dal.database     import get_db

router = APIRouter()


@router.post("", response_model=PredictResponse)
def predict_price(
    body: PredictRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Run a property price prediction.
    Results are persisted to the database via DAL.
    """
    features = body.model_dump()

    success, result = validate_and_predict(
        features=features,
        user_id=current_user["user_id"],
        db=db,
    )

    if not success:
        raise HTTPException(
            status_code=result.get("code", 400),
            detail=result["errors"],
        )

    return PredictResponse(**result)
