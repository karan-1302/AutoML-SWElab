# backend/services/automl_trainer.py
# Core AutoML engine.
# Trains LinearRegression, RandomForest, and XGBoost in sequence,
# updates progress in the shared store, and picks the best model by R².

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

from utils.store import set_training_job, TRAINING_JOBS

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


def run_automl(user_id: str, df: pd.DataFrame, target_column: str):
    """
    Background function: train all algorithms, update progress, store results.
    Called in a daemon thread from the /train/start router.
    """

    # ── 0. Initialise job state ───────────────────────────────
    set_training_job(user_id, {
        "status":          "running",
        "progress":        {algo: 0 for algo in ALGORITHMS},
        "scores":          {},
        "best_model_name": None,
        "pipeline":        None,
        "target_column":   target_column,
        "feature_columns": [],
    })

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
            job = TRAINING_JOBS[user_id].copy()
            job["progress"][name] = 10
            set_training_job(user_id, job)

            pipe = Pipeline([
                ("preprocessor", preprocessor),
                ("model",        model),
            ])

            # Simulate incremental progress during fitting
            for pct in [30, 60]:
                job = TRAINING_JOBS[user_id].copy()
                job["progress"][name] = pct
                set_training_job(user_id, job)
                time.sleep(0.4)   # small delay so frontend poll can visualise progress

            pipe.fit(X_train, y_train)
            y_pred = pipe.predict(X_test)
            metrics = _score(y_test, y_pred)

            trained_pipelines[name] = pipe
            all_scores[name]        = metrics

            # Mark this algo done in progress
            job = TRAINING_JOBS[user_id].copy()
            job["progress"][name]           = 100
            job["progress"][f"{name}_score"] = metrics["r2"]
            job["scores"][name]             = metrics
            set_training_job(user_id, job)

            if metrics["r2"] > best_r2:
                best_r2   = metrics["r2"]
                best_name = name

        # ── 4. Save best model ────────────────────────────────
        set_training_job(user_id, {
            **TRAINING_JOBS[user_id],
            "status":          "done",
            "best_model_name": best_name,
            "pipeline":        trained_pipelines[best_name],
            "feature_columns": feature_columns,
            "all_scores":      all_scores,
        })

    except Exception as exc:
        job = TRAINING_JOBS.get(user_id, {})
        job["status"] = "error"
        job["error"]  = str(exc)
        set_training_job(user_id, job)
        raise
