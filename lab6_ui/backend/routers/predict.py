# backend/routers/predict.py
# UC-09: Generate Prediction  |  UC-10: Reuse Trained Model
#
# POST /api/predict  → takes property features → runs sklearn pipeline → returns price

import math
import pandas as pd
from fastapi import APIRouter, Depends, HTTPException, status

from models.schemas  import PredictRequest, PredictResponse
from utils.security  import get_current_user
from utils.store     import get_training_job, set_last_prediction

router = APIRouter()


@router.post("", response_model=PredictResponse)
def predict_price(
    body: PredictRequest,
    current_user: dict = Depends(get_current_user),
):
    """
    Run a property price prediction using the best trained pipeline.

    1. Retrieve the saved sklearn Pipeline from the training job store.
    2. Build a single-row DataFrame matching the training feature schema.
    3. Call pipeline.predict() and return the estimated price.
    4. Save the result to LAST_PREDICTIONS so the Explain endpoint can use it.
    """
    # ── 1. Load trained pipeline ──────────────────────────────
    job = get_training_job(current_user["user_id"])
    if not job or job.get("status") != "done":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No trained model found. Please complete AutoML training first.",
        )

    pipeline        = job["pipeline"]
    model_name      = job["best_model_name"]
    feature_columns = job["feature_columns"]
    r2              = job["scores"][model_name]["r2"]

    # ── 2. Build input DataFrame in the correct column order ──
    raw = body.model_dump()

    # Keep only columns the model was trained on
    input_row = {col: raw.get(col) for col in feature_columns}
    input_df  = pd.DataFrame([input_row])

    # ── 3. Predict ────────────────────────────────────────────
    try:
        prediction = float(pipeline.predict(input_df)[0])
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Prediction failed: {exc}",
        )

    # Confidence: simple heuristic — map R² (0–1) to confidence (50–99%)
    confidence = round(50 + max(0.0, min(r2, 1.0)) * 49, 1)

    # ── 4. Save for explainability ────────────────────────────
    set_last_prediction(current_user["user_id"], {
        "predicted_price":  prediction,
        "model_used":       model_name,
        "confidence":       confidence,
        "input_features":   raw,
        "pipeline":         pipeline,
        "feature_columns":  feature_columns,
    })

    return PredictResponse(
        predicted_price=round(prediction, 2),
        model_used=model_name,
        confidence=confidence,
    )
