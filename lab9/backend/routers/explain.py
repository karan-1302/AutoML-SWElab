# lab8/backend/routers/explain.py
# ─────────────────────────────────────────────────────────────
# Thin Router: Explainability
# Unchanged for Lab 8 — explain_bll uses the runtime cache directly.
# ─────────────────────────────────────────────────────────────

from fastapi import APIRouter, Depends, HTTPException, status

from models.schemas   import ExplainResponse
from utils.security   import get_current_user
from bll.explain_bll  import generate_explanation

router = APIRouter()


@router.get("", response_model=ExplainResponse)
@router.get("/latest", response_model=ExplainResponse)
def explain_latest(current_user: dict = Depends(get_current_user)):
    """
    Compute SHAP-based explanation for the most recent prediction.
    Uses the pipeline from the runtime cache.
    """
    success, result = generate_explanation(current_user["user_id"])

    if not success:
        raise HTTPException(
            status_code=result.get("code", 400),
            detail=result["errors"],
        )

    return ExplainResponse(**result)
