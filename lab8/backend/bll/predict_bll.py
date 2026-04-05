# lab8/backend/bll/predict_bll.py
# ─────────────────────────────────────────────────────────────
# Prediction Business Logic Layer
#
# Updated for Lab 8: saves predictions to the database via DAL
# and keeps the pipeline in the runtime cache for explainability.
#
# Business Rules:
#   BR-PRD-01  A trained model must exist before predictions.
#   BR-PRD-02  All required property features must be provided.
#   BR-PRD-03  Numeric fields must fall within valid ranges.
#   BR-PRD-04  Confidence = 50 + R² × 49 (range 50-99%).
#   BR-PRD-05  Predicted price rounded to 2 decimal places.
#   BR-PRD-06  Prediction result saved for explainability.
# ─────────────────────────────────────────────────────────────

from typing import Tuple

import pandas as pd
from sqlalchemy.orm import Session

from dal.repositories.prediction_repository import save_prediction
from utils.store import get_cached_training, cache_prediction


# ── Field-level validation rules ──────────────────────────────

FIELD_RULES = {
    "bedrooms":    {"type": "number", "min": 0,    "max": 20,    "label": "Bedrooms"},
    "bathrooms":   {"type": "number", "min": 0,    "max": 10,    "label": "Bathrooms"},
    "sqft_living": {"type": "number", "min": 1,    "max": 50000, "label": "Living Area (sq ft)"},
    "sqft_lot":    {"type": "number", "min": 1,    "max": 200000,"label": "Lot Size (sq ft)"},
    "floors":      {"type": "number", "min": 1,    "max": 5,     "label": "Floors"},
    "waterfront":  {"type": "number", "min": 0,    "max": 1,     "label": "Waterfront"},
    "view":        {"type": "number", "min": 0,    "max": 4,     "label": "View Quality"},
    "condition":   {"type": "number", "min": 1,    "max": 5,     "label": "Condition"},
    "grade":       {"type": "number", "min": 1,    "max": 13,    "label": "Grade"},
    "yr_built":    {"type": "number", "min": 1800, "max": 2026,  "label": "Year Built"},
    "zipcode":     {"type": "string", "label": "ZIP Code"},
}


def _validate_features(features: dict) -> list[str]:
    """Validate each prediction input field against business rules."""
    errors: list[str] = []

    for key, rule in FIELD_RULES.items():
        value = features.get(key)

        # BR-PRD-02: Required
        if value is None or (isinstance(value, str) and not value.strip()):
            errors.append(f"{rule['label']} is required.")
            continue

        if rule["type"] == "number":
            try:
                num = float(value)
            except (TypeError, ValueError):
                errors.append(f"{rule['label']} must be a valid number.")
                continue

            if num < rule["min"] or num > rule["max"]:
                errors.append(
                    f"{rule['label']} must be between {rule['min']} and {rule['max']}. Got: {num}"
                )

        elif rule["type"] == "string":
            if not str(value).strip():
                errors.append(f"{rule['label']} must not be empty.")

    return errors


# ── Confidence scoring ────────────────────────────────────────

def _compute_confidence(r2: float) -> float:
    """Map R² score (0-1) to a human-readable confidence percentage (50-99%)."""
    return round(50 + max(0.0, min(r2, 1.0)) * 49, 1)


# ── Core BLL function ─────────────────────────────────────────

def validate_and_predict(features: dict, user_id: str, db: Session) -> Tuple[bool, dict]:
    """
    Validate features, run the prediction pipeline, and return the result.
    Saves the prediction to the database via DAL.

    Returns
    -------
    (success, payload)
        On success: (True, {predicted_price, model_used, confidence})
        On failure: (False, {errors: [...], code: int})
    """
    # ── Step 1: Check trained model exists (BR-PRD-01) ────────
    cached = get_cached_training(user_id)
    if not cached or cached.get("status") != "done":
        return False, {
            "errors": ["No trained model found. Please complete AutoML training first."],
            "code": 400,
        }

    # ── Step 2: Validate input features ───────────────────────
    validation_errors = _validate_features(features)
    if validation_errors:
        return False, {"errors": validation_errors, "code": 422}

    # ── Step 3: Build input DataFrame ─────────────────────────
    pipeline        = cached["pipeline"]
    model_name      = cached["best_model_name"]
    feature_columns = cached["feature_columns"]
    r2              = cached["scores"][model_name]["r2"]

    input_row = {col: features.get(col) for col in feature_columns}
    input_df  = pd.DataFrame([input_row])

    # ── Step 4: Run prediction ────────────────────────────────
    try:
        prediction = float(pipeline.predict(input_df)[0])
    except Exception as exc:
        return False, {
            "errors": [f"Prediction failed: {exc}"],
            "code": 500,
        }

    # ── Step 5: Compute confidence ────────────────────────────
    confidence = _compute_confidence(r2)

    # ── Step 6: Save to database via DAL (BR-PRD-06) ──────────
    save_prediction(
        db=db,
        user_id=user_id,
        predicted_price=round(prediction, 2),
        model_used=model_name,
        confidence=confidence,
        input_features=features,
    )

    # ── Step 7: Cache for explainability ──────────────────────
    cache_prediction(user_id, {
        "predicted_price":  prediction,
        "model_used":       model_name,
        "confidence":       confidence,
        "input_features":   features,
        "pipeline":         pipeline,
        "feature_columns":  feature_columns,
    })

    # ── Step 8: Return response ───────────────────────────────
    return True, {
        "predicted_price": round(prediction, 2),
        "model_used":      model_name,
        "confidence":      confidence,
    }
