# backend/models/schemas.py
# Pydantic v2 request / response schemas for all routers.
# Validates data at the API/Router layer boundary (Layer 2).

from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional


# ── Auth (UC-01: Login) ───────────────────────────────────────
class LoginRequest(BaseModel):
    email:    str
    password: str

class UserOut(BaseModel):
    user_id: str
    email:   str
    name:    str

class LoginResponse(BaseModel):
    access_token: str
    token_type:   str = "bearer"
    user:         UserOut


# ── Ingest (UC-02: Upload, UC-03: View Dataset) ───────────────
class IngestResponse(BaseModel):
    dataset_id: str
    filename:   str
    columns:    List[str]
    row_count:  int
    preview:    List[Dict[str, Any]]   # first 10 rows as list of dicts


# ── Training (UC-05/06/07/08) ─────────────────────────────────
class TrainStartRequest(BaseModel):
    dataset_id:    str
    target_column: str

class ModelScore(BaseModel):
    name: str
    r2:   float
    rmse: float
    mae:  float

class TrainStatusResponse(BaseModel):
    status:     str                              # 'running' | 'done' | 'error'
    progress:   Dict[str, Any]                   # { algo: pct }
    complete:   bool
    best_model: Optional[ModelScore] = None
    all_models: Optional[List[ModelScore]] = None


# ── Prediction (UC-09) ────────────────────────────────────────
class PredictRequest(BaseModel):
    """
    Flexible prediction request — accepts any feature dict.
    The router maps these to the columns the model was trained on.
    """
    features: Dict[str, Any]

class PredictResponse(BaseModel):
    predicted_price: float
    model_used:      str
    confidence:      float   # heuristic: 50 + R² * 49


# ── Explainability (UC-10/11) ─────────────────────────────────
class ShapEntry(BaseModel):
    feature: str
    value:   float   # positive = pushes price up, negative = pushes price down

class ExplainResponse(BaseModel):
    predicted_price:  float
    model_used:       str
    shap_values:      List[ShapEntry]
    recommendations:  List[str]
