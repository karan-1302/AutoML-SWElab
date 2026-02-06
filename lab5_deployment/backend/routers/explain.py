# backend/routers/explain.py
# Layer 2: Explainability router
# GET /api/explain/latest  →  BLL Explainer.computeSHAP()  →  returns SHAP values
# Maps to UC-10: View Explanation, UC-11: Get Recommendations  (Lab 4 Section V)

import numpy as np
import pandas as pd
from fastapi import APIRouter, Depends, HTTPException, status

from models.schemas import ExplainResponse, ShapEntry
from utils.security import get_current_user
from utils.store    import get_last_prediction

router = APIRouter()


@router.get("/latest", response_model=ExplainResponse)
def explain_latest(current_user: dict = Depends(get_current_user)):
    """
    Return SHAP-based explanation for the most recent prediction.

    Layer flow (Lab 4 Section II — Process 5.0: Explainer):
      Layer 2 receives request
      → BLL Explainer.computeSHAP() calculates feature contributions
      → BLL Explainer.generateReport() builds recommendations
      → Layer 2 returns explanation to React (ExplainPage)
    """
    cached = get_last_prediction(current_user["user_id"])
    if not cached:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No prediction found. Run a prediction first via POST /api/predict.",
        )

    pipeline        = cached["pipeline"]
    feature_columns = cached["feature_columns"]
    input_features  = cached["input_features"]
    predicted_price = cached["predicted_price"]
    model_name      = cached["model_used"]

    # ── BLL: Explainer.computeSHAP() ─────────────────────────
    input_row = {col: input_features.get(col) for col in feature_columns}
    input_df  = pd.DataFrame([input_row])

    shap_entries = _compute_feature_contributions(pipeline, input_df, feature_columns)

    # ── BLL: Explainer.getRecommendations() ──────────────────
    recommendations = _generate_recommendations(shap_entries, predicted_price)

    return ExplainResponse(
        predicted_price=round(predicted_price, 2),
        model_used=model_name,
        shap_values=shap_entries,
        recommendations=recommendations,
    )


# ── BLL helpers ───────────────────────────────────────────────

def _compute_feature_contributions(
    pipeline, input_df: pd.DataFrame, feature_columns: list
) -> list[ShapEntry]:
    """
    Approximate SHAP values using built-in feature importances.

    For tree-based models (RandomForest, XGBoost) we use feature_importances_.
    For linear models we use the absolute coefficient values.
    Both are scaled so the top contributor has a magnitude of 1.0.

    A full SHAP TreeExplainer would be used in production; this approach
    avoids the shap library dependency for the deployment demo.
    """
    model        = pipeline.named_steps["model"]
    preprocessor = pipeline.named_steps["preprocessor"]

    try:
        transformed = preprocessor.transform(input_df)
        feat_names  = preprocessor.get_feature_names_out()
    except Exception:
        return []

    importances = None
    if hasattr(model, "feature_importances_"):
        importances = model.feature_importances_
    elif hasattr(model, "coef_"):
        coef = model.coef_
        importances = np.abs(coef.flatten())

    if importances is None or len(importances) != len(feat_names):
        return []

    # Scale to [-1, 1] range for display
    max_imp = max(abs(importances)) or 1.0
    scaled  = importances / max_imp

    # Map transformed feature names back to original column names
    entries = []
    for fname, imp in zip(feat_names, scaled):
        # Strip sklearn prefixes like "num__" or "cat__"
        clean = fname.split("__", 1)[-1] if "__" in fname else fname
        entries.append(ShapEntry(feature=clean, value=round(float(imp), 4)))

    # Return top 8 by absolute impact
    entries.sort(key=lambda e: abs(e.value), reverse=True)
    return entries[:8]


def _generate_recommendations(
    shap_entries: list[ShapEntry], predicted_price: float
) -> list[str]:
    """
    BLL: Explainer.getRecommendations()
    Produce plain-English business advice based on the top feature drivers.
    """
    recs = []

    if not shap_entries:
        return ["No feature data available to generate recommendations."]

    top = shap_entries[0]
    recs.append(
        f"The strongest price driver is '{top.feature}' "
        f"({'positive' if top.value > 0 else 'negative'} impact)."
    )

    positive = [e for e in shap_entries if e.value > 0.1]
    negative = [e for e in shap_entries if e.value < -0.1]

    if positive:
        names = ", ".join(e.feature for e in positive[:3])
        recs.append(f"Features adding value: {names}.")

    if negative:
        names = ", ".join(e.feature for e in negative[:3])
        recs.append(
            f"Features reducing value: {names}. "
            "Improving these could increase the estimated price."
        )

    if predicted_price > 500_000:
        recs.append("This property is in the premium segment (>$500k).")
    elif predicted_price > 250_000:
        recs.append("This property is in the mid-market segment ($250k–$500k).")
    else:
        recs.append("This property is in the entry-level segment (<$250k).")

    return recs
