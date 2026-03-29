# lab7/backend/routers/explain.py
# ─────────────────────────────────────────────────────────────
# Thin Router: Explainability
# Delegates all business logic to bll/explain_bll.py
# ─────────────────────────────────────────────────────────────

from fastapi import APIRouter, Depends, HTTPException, status

from models.schemas   import ExplainResponse
from utils.security   import get_current_user
from bll.explain_bll  import generate_explanation

router = APIRouter()


@router.get("/latest", response_model=ExplainResponse)
def explain_latest(current_user: dict = Depends(get_current_user)):
    """
    Compute SHAP-based explanation for the most recent prediction.
    All SHAP computation, feature aggregation, and recommendation
    generation are handled by the Business Logic Layer (explain_bll).
    """
    success, result = generate_explanation(current_user["user_id"])

    if not success:
        raise HTTPException(
            status_code=result.get("code", 400),
            detail=result["errors"],
        )

    return ExplainResponse(**result)
