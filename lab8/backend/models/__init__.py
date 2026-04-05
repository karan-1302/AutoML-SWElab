# backend/models/schemas.py
# Pydantic v2 schemas used across all routers.

from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional


# ── Auth ──────────────────────────────────────────────────────
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


# ── Ingest ────────────────────────────────────────────────────
class IngestResponse(BaseModel):
    dataset_id: str
    filename:   str
    columns:    List[str]
    row_count:  int
    preview:    List[Dict[str, Any]]   # first N rows as list of dicts


# ── Training ─────────────────────────────────────────────────
class TrainStartRequest(BaseModel):
    dataset_id:    str
    target_column: str

class ModelScore(BaseModel):
    name: str
    r2:   float
    rmse: float
    mae:  float

class TrainStatusResponse(BaseModel):
    status:     str                        # 'running' | 'done' | 'error'
    progress:   Dict[str, Any]             # { algo: pct, algo_score: float }
    complete:   bool
    best_model: Optional[ModelScore] = None
    all_models: Optional[List[ModelScore]] = None


# ── Prediction ────────────────────────────────────────────────
class PredictRequest(BaseModel):
    bedrooms:    float = Field(..., ge=0, le=20)
    bathrooms:   float = Field(..., ge=0, le=10)
    sqft_living: float = Field(..., ge=1)
    sqft_lot:    float = Field(..., ge=1)
    floors:      float = Field(..., ge=1, le=5)
    waterfront:  int   = Field(0, ge=0, le=1)
    view:        int   = Field(0, ge=0, le=4)
    condition:   int   = Field(..., ge=1, le=5)
    grade:       int   = Field(..., ge=1, le=13)
    yr_built:    int   = Field(..., ge=1800, le=2025)
    zipcode:     str


class PredictResponse(BaseModel):
    predicted_price: float
    model_used:      str
    confidence:      float   # rough confidence % based on R²


# ── Explainability ────────────────────────────────────────────
class ShapEntry(BaseModel):
    feature: str
    value:   float          # SHAP value (positive = price ↑, negative = price ↓)

class ExplainResponse(BaseModel):
    shap_values:     List[ShapEntry]
    recommendations: List[str]
