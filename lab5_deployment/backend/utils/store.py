# backend/utils/store.py
# Layer 4 (DAL): In-memory data store.
#
# In the deployment plan this maps to:
#   D1 — User Database      → Supabase PostgreSQL  (simulated here with USERS dict)
#   D2 — Dataset Storage    → Supabase + file disk  (simulated with DATASETS dict)
#   D3 — Model Registry     → DagsHub MLflow        (simulated with TRAINING_JOBS dict)
#
# Swap each section for a real DB/MLflow call when deploying to Render + Supabase.

import threading
from typing import Dict, Any, Optional

_lock = threading.Lock()

# ── D1: User Database ─────────────────────────────────────────
# Pre-seeded demo user.  In production: query Supabase `users` table.
# Password "password123" — hash generated once at setup time, not at import.
# To regenerate:  python3 -c "from passlib.context import CryptContext; print(CryptContext(schemes=['bcrypt']).hash('password123'))"
USERS: Dict[str, Dict] = {
    "demo@realestate.com": {
        "user_id":         "user-001",
        "email":           "demo@realestate.com",
        "name":            "Demo Agent",
        # bcrypt hash of "password123"
        "hashed_password": "$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",
    }
}

# ── D2: Dataset Storage ───────────────────────────────────────
# { dataset_id: { filename, columns, dataframe, row_count } }
# In production: metadata in Supabase `datasets` table; CSV on Supabase Storage.
DATASETS: Dict[str, Dict] = {}

# ── D3: Model Registry ────────────────────────────────────────
# Holds the latest training job per user_id.
# In production: model .pkl uploaded to DagsHub MLflow; metadata in Supabase.
TRAINING_JOBS: Dict[str, Dict] = {}

# ── Last prediction cache ─────────────────────────────────────
LAST_PREDICTIONS: Dict[str, Dict] = {}


# ── Accessor helpers ──────────────────────────────────────────
def get_user(email: str) -> Optional[Dict]:
    return USERS.get(email)

def get_dataset(dataset_id: str) -> Optional[Dict]:
    return DATASETS.get(dataset_id)

def set_dataset(dataset_id: str, data: Dict):
    with _lock:
        DATASETS[dataset_id] = data

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
