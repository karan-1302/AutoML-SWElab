# lab7/backend/routers/predict.py
# ─────────────────────────────────────────────────────────────
# Thin Router: Prediction
# Delegates all business logic to bll/predict_bll.py
# ─────────────────────────────────────────────────────────────

from fastapi import APIRouter, Depends, HTTPException, status

from models.schemas   import PredictRequest, PredictResponse
from utils.security   import get_current_user
from bll.predict_bll  import validate_and_predict

router = APIRouter()


@router.post("", response_model=PredictResponse)
def predict_price(
    body: PredictRequest,
    current_user: dict = Depends(get_current_user),
):
    """
    Run a property price prediction.
    The router is a thin HTTP layer — all validation,
    prediction logic, confidence scoring, and result storage
    are handled by the Business Logic Layer (predict_bll).
    """
    features = body.model_dump()

    success, result = validate_and_predict(
        features=features,
        user_id=current_user["user_id"],
    )

    if not success:
        raise HTTPException(
            status_code=result.get("code", 400),
            detail=result["errors"],
        )

    return PredictResponse(**result)
