# lab7/backend/bll/predict_bll.py
# ─────────────────────────────────────────────────────────────
# Prediction Business Logic Layer
#
# Business Rules Implemented:
#   BR-PRD-01  A trained model must exist before predictions can be made.
#   BR-PRD-02  All required property features must be provided.
#   BR-PRD-03  Numeric fields must fall within valid ranges.
#   BR-PRD-04  Confidence score is computed as: 50 + R² × 49 (range 50-99%).
#   BR-PRD-05  Predicted price is rounded to 2 decimal places.
#   BR-PRD-06  Prediction result is saved for explainability (downstream use).
#   BR-PRD-07  Waterfront must be 0 or 1; View 0-4; Condition 1-5; Grade 1-13.
#   BR-PRD-08  Year built must be between 1800 and current year.
#   BR-PRD-09  ZIP code must be a non-empty string.
#
# Data Transformation:
#   DT-PRD-01  Form input dict → single-row DataFrame matching training schema.
#   DT-PRD-02  Raw sklearn prediction array → rounded float price.
#   DT-PRD-03  R² score → confidence percentage (human-readable).
# ─────────────────────────────────────────────────────────────

from typing import Tuple

import pandas as pd

from utils.store import get_training_job, set_last_prediction


# ── Field-level validation rules (BR-PRD-03, BR-PRD-07-09) ───

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


# ── Confidence scoring (BR-PRD-04, DT-PRD-03) ────────────────

def _compute_confidence(r2: float) -> float:
    """Map R² score (0-1) to a human-readable confidence percentage (50-99%)."""
    return round(50 + max(0.0, min(r2, 1.0)) * 49, 1)


# ── Core BLL function ─────────────────────────────────────────

def validate_and_predict(features: dict, user_id: str) -> Tuple[bool, dict]:
    """
    Validate features, run the prediction pipeline, and return the result.

    Returns
    -------
    (success, payload)
        On success: (True, {predicted_price, model_used, confidence, field_validations})
        On failure: (False, {errors: [...], code: int, field_errors: {field: msg}})
    """
    # ── Step 1: Check trained model exists (BR-PRD-01) ────────
    job = get_training_job(user_id)
    if not job or job.get("status") != "done":
        return False, {
            "errors": ["No trained model found. Please complete AutoML training first."],
            "code": 400,
        }

    # ── Step 2: Validate input features (BR-PRD-02, BR-PRD-03) ─
    validation_errors = _validate_features(features)
    if validation_errors:
        return False, {"errors": validation_errors, "code": 422}

    # ── Step 3: Build input DataFrame (DT-PRD-01) ────────────
    pipeline        = job["pipeline"]
    model_name      = job["best_model_name"]
    feature_columns = job["feature_columns"]
    r2              = job["scores"][model_name]["r2"]

    input_row = {col: features.get(col) for col in feature_columns}
    input_df  = pd.DataFrame([input_row])

    # ── Step 4: Run prediction (DT-PRD-02) ────────────────────
    try:
        prediction = float(pipeline.predict(input_df)[0])
    except Exception as exc:
        return False, {
            "errors": [f"Prediction failed: {exc}"],
            "code": 500,
        }

    # ── Step 5: Compute confidence (BR-PRD-04) ────────────────
    confidence = _compute_confidence(r2)

    # ── Step 6: Save for explainability (BR-PRD-06) ───────────
    set_last_prediction(user_id, {
        "predicted_price":  prediction,
        "model_used":       model_name,
        "confidence":       confidence,
        "input_features":   features,
        "pipeline":         pipeline,
        "feature_columns":  feature_columns,
    })

    # ── Step 7: Return formatted response (BR-PRD-05) ─────────
    return True, {
        "predicted_price": round(prediction, 2),
        "model_used":      model_name,
        "confidence":      confidence,
    }
