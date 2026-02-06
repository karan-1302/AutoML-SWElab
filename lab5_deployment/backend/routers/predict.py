# backend/routers/predict.py
# ─────────────────────────────────────────────────────────────
# KEY MODULE 2: Prediction Router  (Layer 2 — API / Router Layer)
# ─────────────────────────────────────────────────────────────
#
# Implements the full prediction flow from Lab 4 Section II:
#
#   "When a user asks for a prediction:"
#   1. User enters property details in React
#   2. React sends POST /api/predict
#   3. API layer receives it                          ← this file
#   4. BLL preprocesses the input data               ← pipeline.predict()
#   5. DAL loads the trained model from D3            ← get_training_job()
#   6. BLL runs the model to get a prediction         ← pipeline.predict()
#   7. BLL calculates SHAP values to explain it       ← /api/explain/latest
#   8. API returns prediction + explanation           ← PredictResponse
#   9. React displays the results
#
# Maps to Use Case UC-09: Generate Prediction (Lab 4 Table, Section V)
#
# Endpoint
# --------
#   POST /api/predict
#   Authorization: Bearer <JWT>
#   Body: { "features": { "bedrooms": 3, "sqft_living": 1800, ... } }

import pandas as pd
from fastapi import APIRouter, Depends, HTTPException, status

from models.schemas import PredictRequest, PredictResponse
from utils.security import get_current_user
from utils.store    import get_training_job, set_last_prediction

router = APIRouter()


@router.post("", response_model=PredictResponse)
def predict_price(
    body: PredictRequest,
    current_user: dict = Depends(get_current_user),
):
    """
    Generate a property price prediction.

    Layer flow
    ----------
    Layer 2 (this router)
        → validates JWT and request body
        → calls Layer 3 (BLL) via the stored sklearn Pipeline
        → calls Layer 4 (DAL) via get_training_job() to load the model
        → returns the prediction to the React frontend (Layer 1)

    The sklearn Pipeline itself encapsulates the BLL preprocessing +
    model inference steps (AutoMLTrainer from Lab 4 Section III).
    """

    # ── Layer 4 (DAL): load model from D3 ────────────────────
    # In production this would be: mlflow.pyfunc.load_model(model_uri)
    # Here it reads from the in-memory store populated by run_automl().
    job = get_training_job(current_user["user_id"])

    if not job or job.get("status") != "done":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "No trained model found for your account. "
                "Please complete AutoML training first via POST /api/train/start."
            ),
        )

    pipeline        = job["pipeline"]          # sklearn Pipeline (preprocessor + model)
    model_name      = job["best_model_name"]   # e.g. "RandomForest"
    feature_columns = job["feature_columns"]   # columns the model was trained on
    r2              = job["all_scores"][model_name]["r2"]

    # ── Layer 3 (BLL): preprocess input + run inference ──────
    # Build a single-row DataFrame in the exact column order the model expects.
    # Missing features default to None; the preprocessor's SimpleImputer handles them.
    input_row = {col: body.features.get(col) for col in feature_columns}
    input_df  = pd.DataFrame([input_row])

    try:
        prediction = float(pipeline.predict(input_df)[0])
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Model inference failed: {exc}",
        )

    # Confidence heuristic: map R² (0–1) → confidence (50–99 %)
    # A model with R²=1.0 → 99 % confidence; R²=0.0 → 50 % confidence.
    confidence = round(50.0 + max(0.0, min(r2, 1.0)) * 49.0, 1)

    # ── Layer 4 (DAL): cache result for the Explain endpoint ─
    # The /api/explain/latest router reads this to compute SHAP values.
    set_last_prediction(current_user["user_id"], {
        "predicted_price":  prediction,
        "model_used":       model_name,
        "confidence":       confidence,
        "input_features":   body.features,
        "pipeline":         pipeline,
        "feature_columns":  feature_columns,
    })

    # ── Layer 2: return response to Layer 1 (React) ──────────
    return PredictResponse(
        predicted_price=round(prediction, 2),
        model_used=model_name,
        confidence=confidence,
    )
