# lab8/backend/services/automl_trainer.py
# ─────────────────────────────────────────────────────────────
# Core AutoML engine.
#
# Updated for Lab 8: stores training progress and results in both
# the runtime cache (for real-time polling) and the database (via
# DAL) for persistence.
# ─────────────────────────────────────────────────────────────

import math
import time
import numpy as np
import pandas as pd

from sklearn.model_selection    import train_test_split
from sklearn.pipeline           import Pipeline
from sklearn.compose            import ColumnTransformer
from sklearn.preprocessing      import StandardScaler, OneHotEncoder
from sklearn.impute             import SimpleImputer
from sklearn.linear_model       import LinearRegression
from sklearn.ensemble           import RandomForestRegressor
from sklearn.metrics            import mean_squared_error, mean_absolute_error, r2_score
from xgboost                    import XGBRegressor

from utils.store import cache_training, get_cached_training, TRAINING_CACHE
from dal.database import SessionLocal
from dal.repositories.training_job_repository import create_or_update_job

ALGORITHMS = ["LinearRegression", "RandomForest", "XGBoost"]


def _build_preprocessor(X: pd.DataFrame) -> ColumnTransformer:
    """Build a sklearn ColumnTransformer for numeric + categorical features."""
    numeric_cols     = X.select_dtypes(include=["int64", "float64"]).columns.tolist()
    categorical_cols = X.select_dtypes(include=["object",  "category"]).columns.tolist()

    numeric_pipe = Pipeline([
        ("imputer", SimpleImputer(strategy="median")),
        ("scaler",  StandardScaler()),
    ])
    categorical_pipe = Pipeline([
        ("imputer", SimpleImputer(strategy="constant", fill_value="Unknown")),
        ("onehot",  OneHotEncoder(handle_unknown="ignore", sparse_output=False)),
    ])

    transformers = []
    if numeric_cols:
        transformers.append(("num", numeric_pipe, numeric_cols))
    if categorical_cols:
        transformers.append(("cat", categorical_pipe, categorical_cols))

    return ColumnTransformer(transformers=transformers, remainder="drop")


def _score(y_true, y_pred):
    """Return dict of regression metrics."""
    mse  = mean_squared_error(y_true, y_pred)
    rmse = math.sqrt(mse)
    mae  = mean_absolute_error(y_true, y_pred)
    r2   = r2_score(y_true, y_pred)
    return {"rmse": round(rmse, 4), "mae": round(mae, 4), "r2": round(r2, 6)}


def _update_cache(user_id: str, data: dict):
    """Update the runtime training cache."""
    existing = get_cached_training(user_id) or {}
    existing.update(data)
    cache_training(user_id, existing)


def run_automl(user_id: str, df: pd.DataFrame, target_column: str):
    """
    Background function: train all algorithms, update progress, store results.
    Updates both the runtime cache and the database.
    """

    # ── 0. Initialise job state ───────────────────────────────
    initial_state = {
        "status":          "running",
        "progress":        {algo: 0 for algo in ALGORITHMS},
        "scores":          {},
        "best_model_name": None,
        "pipeline":        None,
        "target_column":   target_column,
        "feature_columns": [],
    }
    cache_training(user_id, initial_state)

    try:
        # ── 1. Prepare data ───────────────────────────────────
        if target_column not in df.columns:
            raise ValueError(f"Target column '{target_column}' not found in dataset.")

        df = df.dropna(subset=[target_column]).copy()
        X  = df.drop(columns=[target_column])
        y  = df[target_column].astype(float)

        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.20, random_state=42
        )

        preprocessor    = _build_preprocessor(X_train)
        feature_columns = X.columns.tolist()

        # ── 2. Define candidate models ────────────────────────
        candidates = {
            "LinearRegression": LinearRegression(),
            "RandomForest":     RandomForestRegressor(n_estimators=100, random_state=42, n_jobs=-1),
            "XGBoost":          XGBRegressor(n_estimators=100, random_state=42,
                                             verbosity=0, eval_metric="rmse"),
        }

        trained_pipelines = {}
        all_scores        = {}
        best_r2           = -float("inf")
        best_name         = ""

        # ── 3. Training loop ──────────────────────────────────
        for step, (name, model) in enumerate(candidates.items()):
            # Update progress: starting this algo
            cached = get_cached_training(user_id) or {}
            progress = cached.get("progress", {})
            progress[name] = 10
            _update_cache(user_id, {"progress": progress})

            pipe = Pipeline([
                ("preprocessor", preprocessor),
                ("model",        model),
            ])

            # Simulate incremental progress
            for pct in [30, 60]:
                cached = get_cached_training(user_id) or {}
                progress = cached.get("progress", {})
                progress[name] = pct
                _update_cache(user_id, {"progress": progress})
                time.sleep(0.4)

            pipe.fit(X_train, y_train)
            y_pred = pipe.predict(X_test)
            metrics = _score(y_test, y_pred)

            trained_pipelines[name] = pipe
            all_scores[name]        = metrics

            # Mark this algo done in progress
            cached = get_cached_training(user_id) or {}
            progress = cached.get("progress", {})
            scores = cached.get("scores", {})
            progress[name]           = 100
            progress[f"{name}_score"] = metrics["r2"]
            scores[name]             = metrics
            _update_cache(user_id, {"progress": progress, "scores": scores})

            if metrics["r2"] > best_r2:
                best_r2   = metrics["r2"]
                best_name = name

        # ── 4. Save best model ────────────────────────────────
        final_state = {
            "status":          "done",
            "best_model_name": best_name,
            "pipeline":        trained_pipelines[best_name],
            "feature_columns": feature_columns,
            "all_scores":      all_scores,
            "scores":          all_scores,
        }
        _update_cache(user_id, final_state)

        # ── 5. Persist to database via DAL ─────────────────────
        db = SessionLocal()
        try:
            create_or_update_job(
                db=db,
                user_id=user_id,
                status="done",
                progress=get_cached_training(user_id).get("progress", {}),
                scores=all_scores,
                best_model_name=best_name,
                target_column=target_column,
                feature_columns=feature_columns,
            )
        finally:
            db.close()

    except Exception as exc:
        _update_cache(user_id, {"status": "error", "error": str(exc)})

        # Persist error to database
        db = SessionLocal()
        try:
            create_or_update_job(
                db=db,
                user_id=user_id,
                status="error",
                error_message=str(exc),
            )
        finally:
            db.close()

        raise
