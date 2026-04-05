# lab8/backend/utils/store.py
# ─────────────────────────────────────────────────────────────
# In-Memory Runtime Cache
#
# In Lab 8 the persistent metadata (users, datasets, training jobs,
# predictions) is stored in SQLite via the DAL.  However, some
# objects cannot be serialised to a database:
#   - pandas DataFrames  (uploaded CSV data)
#   - sklearn Pipeline objects  (trained ML models)
#
# This module keeps a lightweight runtime cache for those objects.
# It is NOT the primary data store — that role belongs to the DAL.
# ─────────────────────────────────────────────────────────────

from typing import Dict, Any, Optional
import threading

_lock = threading.Lock()

# ── Runtime caches (non-serialisable objects) ─────────────────

# { dataset_id: { "dataframe": pd.DataFrame, "columns": [...], ... } }
DATASETS_CACHE: Dict[str, Dict] = {}

# { user_id: { "pipeline": Pipeline, "feature_columns": [...], ... } }
TRAINING_CACHE: Dict[str, Dict] = {}

# { user_id: { "pipeline": Pipeline, "input_features": {...}, ... } }
PREDICTION_CACHE: Dict[str, Dict] = {}


# ── Dataset cache helpers ─────────────────────────────────────

def cache_dataset(dataset_id: str, data: Dict):
    """Store a DataFrame and metadata in the runtime cache."""
    with _lock:
        DATASETS_CACHE[dataset_id] = data


def get_cached_dataset(dataset_id: str) -> Optional[Dict]:
    """Retrieve cached dataset data."""
    return DATASETS_CACHE.get(dataset_id)


# ── Training cache helpers ────────────────────────────────────

def cache_training(user_id: str, data: Dict):
    """Store a trained pipeline and related data in the runtime cache."""
    with _lock:
        TRAINING_CACHE[user_id] = data


def get_cached_training(user_id: str) -> Optional[Dict]:
    """Retrieve cached training data (pipeline, features, etc.)."""
    return TRAINING_CACHE.get(user_id)


# ── Prediction cache helpers ──────────────────────────────────

def cache_prediction(user_id: str, data: Dict):
    """Store prediction context for explainability in the runtime cache."""
    with _lock:
        PREDICTION_CACHE[user_id] = data


def get_cached_prediction(user_id: str) -> Optional[Dict]:
    """Retrieve cached prediction data for SHAP explanation."""
    return PREDICTION_CACHE.get(user_id)
