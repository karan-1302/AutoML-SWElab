# backend/routers/explain.py
# UC-11: View Explainable Predictions  |  UC-12: Decision-Support Recommendations
#
# GET /api/explain/latest  → computes SHAP values for the last prediction
#                         → generates investment recommendation strings

import numpy as np
import pandas as pd
import shap

from fastapi import APIRouter, Depends, HTTPException, status

from models.schemas  import ExplainResponse, ShapEntry
from utils.security  import get_current_user
from utils.store     import get_last_prediction, get_training_job

router = APIRouter()


def _generate_recommendations(shap_values: list[dict], predicted_price: float) -> list[str]:
    """
    Generate plain-English investment recommendations based on the top SHAP drivers.
    """
    recs = []

    # Sort by absolute SHAP value
    sorted_shap = sorted(shap_values, key=lambda x: abs(x["value"]), reverse=True)
    top = sorted_shap[:5]

    for entry in top:
        feat = entry["feature"]
        val  = entry["value"]

        if feat in ("sqft_living", "sqft_lot") and val > 0:
            recs.append(
                f"📐 Living area is a strong positive driver (SHAP = +{val:.2f}). "
                "Larger properties command a measurable premium in this market."
            )
        elif feat == "grade" and val > 0:
            recs.append(
                f"🏗️ High construction grade significantly increases value (SHAP = +{val:.2f}). "
                "Consider properties graded 8+ for maximum appreciation potential."
            )
        elif feat == "waterfront" and val > 0:
            recs.append(
                f"🌊 Waterfront access is a top value contributor (SHAP = +{val:.2f}). "
                "Waterfront homes command a strong premium; prioritise this feature if budget allows."
            )
        elif feat == "view" and val > 0:
            recs.append(
                f"🌄 View quality adds measurable value (SHAP = +{val:.2f}). "
                "Properties with unobstructed views of water or greenery retain value over time."
            )
        elif feat == "yr_built" and val < 0:
            recs.append(
                f"🔧 Older construction year is reducing estimated value (SHAP = {val:.2f}). "
                "Renovation investments in older properties may yield positive ROI."
            )
        elif feat == "condition" and val > 0:
            recs.append(
                f"✅ Good physical condition is boosting price (SHAP = +{val:.2f}). "
                "Maintaining or improving condition is a low-cost way to preserve asset value."
            )
        elif feat == "bedrooms" and val > 0:
            recs.append(
                f"🛏️ Bedroom count is a positive pricing signal (SHAP = +{val:.2f}). "
                "Family-sized properties in this zone attract premium buyer segments."
            )
        elif val < 0:
            recs.append(
                f"⚠️ '{feat}' is negatively impacting the estimated price (SHAP = {val:.2f}). "
                "Review this attribute if repositioning the asset for a higher market segment."
            )

    # Price-tier recommendation
    if predicted_price > 700_000:
        recs.append(
            "💰 This property sits in the premium tier (>$700K). "
            "Target high-net-worth buyers and emphasise lifestyle features in marketing."
        )
    elif predicted_price > 400_000:
        recs.append(
            "📈 Mid-market pricing ($400K–$700K) suggests strong demand from young families "
            "and first-time buyers. Standard digital listing channels are recommended."
        )
    else:
        recs.append(
            "🏷️ Entry-level pricing (<$400K) positions this property competitively. "
            "Consider affordable-housing incentives or rental yield analysis."
        )

    return recs[:6]   # Cap at 6 recommendation cards


@router.get("/latest", response_model=ExplainResponse)
def explain_latest(current_user: dict = Depends(get_current_user)):
    """
    Compute SHAP values for the most recent prediction made by this user
    and return them alongside investment recommendations.

    SHAP (SHapley Additive exPlanations) assigns each input feature a
    contribution score indicating how much it pushed the prediction higher
    or lower relative to the model's mean output.
    """
    # ── 1. Load last prediction ───────────────────────────────
    pred = get_last_prediction(current_user["user_id"])
    if not pred:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No prediction found. Please run a prediction first.",
        )

    pipeline        = pred["pipeline"]
    feature_columns = pred["feature_columns"]
    input_features  = pred["input_features"]
    predicted_price = pred["predicted_price"]

    # ── 2. Build input row ────────────────────────────────────
    input_row = {col: input_features.get(col) for col in feature_columns}
    input_df  = pd.DataFrame([input_row])

    # ── 3. Transform input through the preprocessor ──────────
    try:
        preprocessor = pipeline.named_steps["preprocessor"]
        model        = pipeline.named_steps["model"]
        X_transformed = preprocessor.transform(input_df)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Preprocessing failed during SHAP computation: {exc}",
        )

    # ── 4. Compute SHAP values ────────────────────────────────
    try:
        # Use TreeExplainer for tree-based models (fast), LinearExplainer for others
        model_type = type(model).__name__
        if model_type in ("RandomForestRegressor", "XGBRegressor", "GradientBoostingRegressor"):
            explainer   = shap.TreeExplainer(model)
            shap_arr    = explainer.shap_values(X_transformed)
        else:
            explainer   = shap.LinearExplainer(model, X_transformed)
            shap_arr    = explainer.shap_values(X_transformed)

        shap_vals = shap_arr[0] if shap_arr.ndim > 1 else shap_arr

        # ── 5. Map transformed features → original feature names ─
        # For numeric features we can map 1-to-1; for one-hot encoded categorical
        # we aggregate by taking the sum of SHAP values per original column.
        try:
            feature_names_out = preprocessor.get_feature_names_out()
        except Exception:
            feature_names_out = [f"feature_{i}" for i in range(len(shap_vals))]

        # Build aggregated SHAP dict keyed by original feature name
        shap_dict: dict[str, float] = {}
        for fname, sv in zip(feature_names_out, shap_vals):
            # sklearn prepends "num__" or "cat__" to names
            original = fname.split("__")[-1]
            # For OHE columns, strip the category suffix (e.g. "zipcode_98103" → "zipcode")
            base = original.split("_")[0] if original not in feature_columns else original
            # Find best match in original feature columns
            matched = next((c for c in feature_columns if c == original or original.startswith(c)), base)
            shap_dict[matched] = shap_dict.get(matched, 0.0) + float(sv)

    except Exception:
        # Fallback: estimate SHAP via feature sensitivity (finite difference)
        baseline   = float(pipeline.predict(input_df)[0])
        shap_dict  = {}
        for col in feature_columns:
            perturbed_row = input_row.copy()
            try:
                original_val = float(perturbed_row[col]) if perturbed_row[col] is not None else 0.0
                perturbed_row[col] = original_val * 1.10 + 1e-6
            except (TypeError, ValueError):
                continue
            perturbed_df   = pd.DataFrame([perturbed_row])
            perturbed_pred = float(pipeline.predict(perturbed_df)[0])
            shap_dict[col] = round(perturbed_pred - baseline, 4)

    # ── 6. Build response list ────────────────────────────────
    shap_entries = [
        ShapEntry(feature=feat, value=round(val, 6))
        for feat, val in shap_dict.items()
    ]
    # Sort by absolute value descending
    shap_entries.sort(key=lambda e: abs(e.value), reverse=True)

    # ── 7. Generate recommendations ───────────────────────────
    raw_shap = [{"feature": e.feature, "value": e.value} for e in shap_entries]
    recommendations = _generate_recommendations(raw_shap, predicted_price)

    return ExplainResponse(
        shap_values=shap_entries,
        recommendations=recommendations,
    )
