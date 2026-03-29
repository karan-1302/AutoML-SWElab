# backend/utils/store.py
# Lightweight in-memory store that replaces a real DB + model registry
# for this assignment demo. In production this would be Supabase + DagsHub MLflow.

from typing import Dict, Any, Optional
import threading

_lock = threading.Lock()

# ── Simulated user table ──────────────────────────────────────
# Pre-seeded demo user (password = "password123")
from passlib.context import CryptContext
_pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")

USERS: Dict[str, Dict] = {
    "demo@realestate.com": {
        "user_id": "user-001",
        "email":   "demo@realestate.com",
        "name":    "Demo Agent",
        "hashed_password": _pwd.hash("password123"),
    }
}

# ── Uploaded dataset store ────────────────────────────────────
# { dataset_id: { filename, columns, dataframe (pd.DataFrame), row_count } }
DATASETS: Dict[str, Dict] = {}

# ── Training job store ────────────────────────────────────────
# Holds the current / last training job state per user_id
TRAINING_JOBS: Dict[str, Dict] = {}
# Structure:
# {
#   "user-001": {
#     "status": "running" | "done" | "error",
#     "progress": { "LinearRegression": 0-100, "RandomForest": 0-100, "XGBoost": 0-100 },
#     "scores": { "LinearRegression": {"r2":, "rmse":, "mae":}, ... },
#     "best_model_name": "RandomForest",
#     "pipeline": <sklearn Pipeline object>,
#     "target_column": "price",
#     "feature_columns": [...],
#   }
# }

# ── Last prediction store ─────────────────────────────────────
LAST_PREDICTIONS: Dict[str, Dict] = {}
# { user_id: { predicted_price, model_used, confidence, input_features, shap_values } }


def get_user(email: str) -> Optional[Dict]:
    return USERS.get(email)

def get_training_job(user_id: str) -> Optional[Dict]:
    return TRAINING_JOBS.get(user_id)

def set_training_job(user_id: str, data: Dict):
    with _lock:
        TRAINING_JOBS[user_id] = data

def get_last_prediction(user_id: str) -> Optional[Dict]:
    return LAST_PREDICTIONS.get(user_id)

def set_last_prediction(user_id: str, data: Dict):
    with _lock:
        LAST_PREDICTIONS[user_id] = data
