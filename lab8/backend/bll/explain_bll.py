# lab8/backend/bll/explain_bll.py
# ─────────────────────────────────────────────────────────────
# Explainability Business Logic Layer
#
# Updated for Lab 8: accesses prediction data from the runtime
# cache (which holds the pipeline for SHAP computation).
#
# Business Rules:
#   BR-EXP-01  A prediction must exist before explanation.
#   BR-EXP-02  SHAP values computed using TreeExplainer for tree models.
#   BR-EXP-03  LinearExplainer for non-tree models.
#   BR-EXP-04  Fallback: finite-difference sensitivity.
#   BR-EXP-05  One-hot features aggregated back to original names.
#   BR-EXP-06  Recommendations capped at 6.
#   BR-EXP-07  Price tier: Premium (>$700K), Mid ($400K-$700K), Entry (<$400K).
#   BR-EXP-08  SHAP values sorted by absolute value.
# ─────────────────────────────────────────────────────────────

from typing import Tuple, List

import numpy as np
import pandas as pd
import shap

from models.schemas import ShapEntry
from utils.store import get_cached_prediction


# ── Recommendation engine ─────────────────────────────────────

def _generate_recommendations(shap_values: list[dict], predicted_price: float) -> list[str]:
    """Generate plain-English investment recommendations based on top SHAP drivers."""
    recs: list[str] = []
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

    # BR-EXP-07: Price tier classification
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

    return recs[:6]   # BR-EXP-06


# ── SHAP computation ─────────────────────────────────────────

def _compute_shap_values(pipeline, feature_columns, input_features) -> dict:
    """Compute SHAP values from the trained pipeline."""
    input_row = {col: input_features.get(col) for col in feature_columns}
    input_df  = pd.DataFrame([input_row])

    try:
        preprocessor = pipeline.named_steps["preprocessor"]
        model        = pipeline.named_steps["model"]
        X_transformed = preprocessor.transform(input_df)

        model_type = type(model).__name__
        if model_type in ("RandomForestRegressor", "XGBRegressor", "GradientBoostingRegressor"):
            explainer = shap.TreeExplainer(model)
        else:
            explainer = shap.LinearExplainer(model, X_transformed)

        shap_arr  = explainer.shap_values(X_transformed)
        shap_vals = shap_arr[0] if shap_arr.ndim > 1 else shap_arr

        try:
            feature_names_out = preprocessor.get_feature_names_out()
        except Exception:
            feature_names_out = [f"feature_{i}" for i in range(len(shap_vals))]

        shap_dict: dict[str, float] = {}
        for fname, sv in zip(feature_names_out, shap_vals):
            original = fname.split("__")[-1]
            base = original.split("_")[0] if original not in feature_columns else original
            matched = next((c for c in feature_columns if c == original or original.startswith(c)), base)
            shap_dict[matched] = shap_dict.get(matched, 0.0) + float(sv)

        return shap_dict

    except Exception:
        # BR-EXP-04: Fallback — finite-difference sensitivity
        baseline  = float(pipeline.predict(input_df)[0])
        shap_dict = {}
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

        return shap_dict


# ── Core BLL function ─────────────────────────────────────────

def generate_explanation(user_id: str) -> Tuple[bool, dict]:
    """
    Generate SHAP-based explanation and investment recommendations.
    Uses the pipeline from the runtime cache.

    Returns
    -------
    (success, payload)
        On success: (True, {shap_values: [ShapEntry], recommendations: [str]})
        On failure: (False, {errors: [...], code: int})
    """
    # ── Step 1: Load last prediction from cache (BR-EXP-01) ──
    pred = get_cached_prediction(user_id)
    if not pred:
        return False, {
            "errors": ["No prediction found. Please run a prediction first."],
            "code": 404,
        }

    # ── Step 2: Compute SHAP ──────────────────────────────────
    shap_dict = _compute_shap_values(
        pipeline=pred["pipeline"],
        feature_columns=pred["feature_columns"],
        input_features=pred["input_features"],
    )

    # ── Step 3: Build sorted ShapEntry list ───────────────────
    shap_entries = [
        ShapEntry(feature=feat, value=round(val, 6))
        for feat, val in shap_dict.items()
    ]
    shap_entries.sort(key=lambda e: abs(e.value), reverse=True)

    # ── Step 4: Generate recommendations ──────────────────────
    raw_shap = [{"feature": e.feature, "value": e.value} for e in shap_entries]
    recommendations = _generate_recommendations(raw_shap, pred["predicted_price"])

    return True, {
        "shap_values":     shap_entries,
        "recommendations": recommendations,
    }
