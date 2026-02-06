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
import os
import threading
import json
import joblib
from datetime import datetime, timezone
from pathlib import Path

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

# ── Optional MLflow integration ───────────────────────────────
MLFLOW_ENABLED = False
MLFLOW_TIMEOUT = 10  # seconds
try:
    import mlflow
    mlflow_uri = os.getenv("MLFLOW_TRACKING_URI")
    if mlflow_uri:
        try:
            mlflow.set_tracking_uri(mlflow_uri)
            MLFLOW_ENABLED = True
            print("[MLFLOW] ✅ MLflow tracking enabled")
        except Exception as e:
            print(f"[MLFLOW] ⚠️  Could not set MLflow tracking URI: {str(e)}")
    else:
        print("[MLFLOW] ⚠️  MLFLOW_TRACKING_URI not set, MLflow logging disabled")
except ImportError:
    print("[MLFLOW] ⚠️  MLflow not installed, logging disabled")


def _log_metric_with_timeout(metric_name: str, value: float, timeout: int = MLFLOW_TIMEOUT) -> bool:
    """
    Log a metric to MLflow with a timeout wrapper.
    Returns True if successful, False if timeout or error.
    """
    if not MLFLOW_ENABLED:
        return False
    
    result = {"success": False}
    
    def log_task():
        try:
            mlflow.log_metric(metric_name, value)
            result["success"] = True
        except Exception as e:
            print(f"[MLFLOW] Error logging {metric_name}: {str(e)}")
            result["success"] = False
    
    # Run logging in a separate thread with timeout
    thread = threading.Thread(target=log_task, daemon=True)
    thread.start()
    thread.join(timeout=timeout)
    
    if thread.is_alive():
        print(f"[MLFLOW] ⚠️  Timeout logging {metric_name} (>{timeout}s), skipping")
        return False
    
    return result["success"]


def _set_tag_with_timeout(tag_name: str, value: str, timeout: int = MLFLOW_TIMEOUT) -> bool:
    """
    Set a tag in MLflow with a timeout wrapper.
    Returns True if successful, False if timeout or error.
    """
    if not MLFLOW_ENABLED:
        return False
    
    result = {"success": False}
    
    def tag_task():
        try:
            mlflow.set_tag(tag_name, value)
            result["success"] = True
        except Exception as e:
            print(f"[MLFLOW] Error setting tag {tag_name}: {str(e)}")
            result["success"] = False
    
    # Run tag setting in a separate thread with timeout
    thread = threading.Thread(target=tag_task, daemon=True)
    thread.start()
    thread.join(timeout=timeout)
    
    if thread.is_alive():
        print(f"[MLFLOW] ⚠️  Timeout setting tag {tag_name} (>{timeout}s), skipping")
        return False
    
    return result["success"]

ALGORITHMS = ["LinearRegression", "RandomForest", "XGBoost"]


def _save_model_to_disk(
    user_id: str,
    dataset_id: str,
    target_column: str,
    model_name: str,
    pipeline: Pipeline,
    feature_columns: list,
    scores: dict,
) -> str:
    """
    Save a trained model pipeline to disk.
    
    Directory structure: models_storage/{user_id}/{dataset_id}/{target_column}/{model_name}.pkl
    Also saves model_info.json with metadata.
    
    Parameters
    ----------
    user_id : str
        User ID for organizing models.
    dataset_id : str
        Dataset ID for organizing models.
    target_column : str
        Target column name.
    model_name : str
        Name of the model (e.g., "XGBoost").
    pipeline : Pipeline
        The trained sklearn pipeline.
    feature_columns : list
        List of feature column names.
    scores : dict
        Dictionary of model scores (r2, rmse, mae).
    
    Returns
    -------
    str
        Path to the saved model file.
    """
    # Create directory structure
    base_dir = Path("models_storage")
    model_dir = base_dir / user_id / dataset_id / target_column
    model_dir.mkdir(parents=True, exist_ok=True)
    
    # Save model pickle
    model_path = model_dir / f"{model_name}.pkl"
    joblib.dump(pipeline, str(model_path))
    print(f"[TRAIN] Model saved to {model_path}")
    
    # Save model metadata
    model_info = {
        "model_name": model_name,
        "scores": scores,
        "feature_columns": feature_columns,
        "target_column": target_column,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    info_path = model_dir / "model_info.json"
    with open(info_path, "w") as f:
        json.dump(model_info, f, indent=2)
    print(f"[TRAIN] Model metadata saved to {info_path}")
    
    return str(model_path)


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


def run_automl(user_id: str, df: pd.DataFrame, target_column: str, dataset_id: str = None):
    """
    Background function: train all algorithms, update progress, store results.
    Updates both the runtime cache and the database.
    Persists the best model to disk.
    
    Includes comprehensive error handling and logging for each training phase.
    Optionally logs to MLflow if configured.
    
    Parameters
    ----------
    user_id : str
        The user ID running the training.
    df : pd.DataFrame
        The training dataset.
    target_column : str
        The target column name.
    dataset_id : str, optional
        The dataset ID for organizing persisted models.
    """
    print(f"[TRAIN] Starting AutoML training for user {user_id}, target: {target_column}, dataset: {dataset_id}")

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
    print(f"[TRAIN] Initialized cache for user {user_id}")

    # ── Optional MLflow setup ─────────────────────────────────
    mlflow_run = None
    if MLFLOW_ENABLED:
        try:
            print(f"[TRAIN] Attempting to start MLflow run...")
            mlflow.start_run(run_name=f"AutoML_{user_id}")
            mlflow.set_tag("user_id", user_id)
            mlflow.set_tag("target_column", target_column)
            mlflow_run = mlflow.active_run()
            print(f"[TRAIN] ✅ MLflow run started: {mlflow_run.info.run_id}")
        except Exception as mlflow_err:
            print(f"[TRAIN] ⚠️  MLflow error (continuing without logging): {type(mlflow_err).__name__}: {str(mlflow_err)}")
            mlflow_run = None

    try:
        # ── 1. Prepare data ───────────────────────────────────
        print(f"[TRAIN] Phase 1: Preparing data...")
        if target_column not in df.columns:
            raise ValueError(f"Target column '{target_column}' not found in dataset.")

        df = df.dropna(subset=[target_column]).copy()
        X  = df.drop(columns=[target_column])
        y  = df[target_column].astype(float)
        print(f"[TRAIN] Data prepared: {X.shape[0]} rows, {X.shape[1]} features")

        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.20, random_state=42
        )
        print(f"[TRAIN] Train/test split: {X_train.shape[0]} train, {X_test.shape[0]} test")

        preprocessor    = _build_preprocessor(X_train)
        feature_columns = X.columns.tolist()
        print(f"[TRAIN] Preprocessor built with {len(feature_columns)} features")

        # ── 2. Define candidate models ────────────────────────
        print(f"[TRAIN] Phase 2: Defining candidate models...")
        candidates = {
            "LinearRegression": LinearRegression(),
            "RandomForest":     RandomForestRegressor(n_estimators=100, random_state=42, n_jobs=-1),
            "XGBoost":          XGBRegressor(n_estimators=100, random_state=42,
                                             verbosity=0, eval_metric="rmse"),
        }
        print(f"[TRAIN] Candidate models defined: {list(candidates.keys())}")

        trained_pipelines = {}
        all_scores        = {}
        best_r2           = -float("inf")
        best_name         = ""

        # ── 3. Training loop ──────────────────────────────────
        print(f"[TRAIN] Phase 3: Starting training loop...")
        for step, (name, model) in enumerate(candidates.items()):
            print(f"[TRAIN] Training {name} ({step+1}/{len(candidates)})...")
            
            try:
                # Update progress: starting this algo
                cached = get_cached_training(user_id) or {}
                progress = cached.get("progress", {})
                progress[name] = 10
                _update_cache(user_id, {"progress": progress})
                print(f"[TRAIN] {name}: Progress 10% (starting)")

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
                    print(f"[TRAIN] {name}: Progress {pct}%")
                    time.sleep(0.4)

                print(f"[TRAIN] {name}: Fitting model...")
                pipe.fit(X_train, y_train)
                print(f"[TRAIN] {name}: Model fitted, generating predictions...")
                
                y_pred = pipe.predict(X_test)
                metrics = _score(y_test, y_pred)
                print(f"[TRAIN] {name}: Metrics - R²={metrics['r2']}, RMSE={metrics['rmse']}, MAE={metrics['mae']}")

                # Log to MLflow if enabled
                if mlflow_run:
                    try:
                        mlflow.log_metric(f"{name}_r2", metrics["r2"])
                        mlflow.log_metric(f"{name}_rmse", metrics["rmse"])
                        mlflow.log_metric(f"{name}_mae", metrics["mae"])
                    except Exception as log_err:
                        print(f"[TRAIN] ⚠️  MLflow logging error for {name}: {str(log_err)}")

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
                print(f"[TRAIN] {name}: Progress 100% (complete)")

                if metrics["r2"] > best_r2:
                    best_r2   = metrics["r2"]
                    best_name = name
                    print(f"[TRAIN] New best model: {best_name} with R²={best_r2}")
                    
            except Exception as model_exc:
                print(f"[TRAIN] ERROR in {name}: {type(model_exc).__name__}: {str(model_exc)}")
                # Update cache to mark this model as failed
                cached = get_cached_training(user_id) or {}
                progress = cached.get("progress", {})
                progress[name] = -1  # Negative indicates error
                _update_cache(user_id, {"progress": progress})
                # Continue to next model instead of crashing
                continue

        # ── 4. Save best model ────────────────────────────────
        print(f"[TRAIN] Phase 4: Saving best model...")
        if not best_name:
            raise ValueError("No models trained successfully")
            
        print(f"[TRAIN] Best model: {best_name} with R²={best_r2}")
        
        # Log best model to MLflow
        if mlflow_run:
            try:
                mlflow.log_metric("best_r2", best_r2)
                mlflow.set_tag("best_model", best_name)
            except Exception as log_err:
                print(f"[TRAIN] ⚠️  MLflow logging error for best model: {str(log_err)}")
        
        # Save model to disk if dataset_id is provided
        model_path = None
        if dataset_id:
            try:
                model_path = _save_model_to_disk(
                    user_id=user_id,
                    dataset_id=dataset_id,
                    target_column=target_column,
                    model_name=best_name,
                    pipeline=trained_pipelines[best_name],
                    feature_columns=feature_columns,
                    scores=all_scores[best_name],
                )
                print(f"[TRAIN] Model persisted to disk: {model_path}")
            except Exception as save_err:
                print(f"[TRAIN] ⚠️  Error saving model to disk: {str(save_err)}")
        
        final_state = {
            "status":          "done",
            "best_model_name": best_name,
            "pipeline":        trained_pipelines[best_name],
            "feature_columns": feature_columns,
            "all_scores":      all_scores,
            "scores":          all_scores,
            "model_path":      model_path,
        }
        _update_cache(user_id, final_state)
        print(f"[TRAIN] Cache updated with final state")

        # ── 5. Persist to database via DAL ─────────────────────
        print(f"[TRAIN] Phase 5: Persisting to database...")
        db = SessionLocal()
        try:
            # Get MLflow run ID if available
            mlflow_run_id = None
            if mlflow_run:
                mlflow_run_id = mlflow_run.info.run_id
            
            create_or_update_job(
                db=db,
                user_id=user_id,
                status="done",
                progress=get_cached_training(user_id).get("progress", {}),
                scores=all_scores,
                best_model_name=best_name,
                target_column=target_column,
                feature_columns=feature_columns,
                mlflow_run_id=mlflow_run_id,
            )
            print(f"[TRAIN] Training job persisted to database")
            if mlflow_run_id:
                print(f"[TRAIN] MLflow run ID saved: {mlflow_run_id}")
        finally:
            db.close()
        
        print(f"[TRAIN] AutoML training completed successfully for user {user_id}")

    except Exception as exc:
        print(f"[TRAIN] FATAL ERROR: {type(exc).__name__}: {str(exc)}")
        import traceback
        traceback.print_exc()
        
        _update_cache(user_id, {"status": "error", "error": str(exc)})
        print(f"[TRAIN] Error state cached for user {user_id}")

        # Log error to MLflow
        if mlflow_run:
            try:
                mlflow.set_tag("error", str(exc))
            except Exception as log_err:
                print(f"[TRAIN] ⚠️  MLflow error logging failed: {str(log_err)}")

        # Persist error to database
        db = SessionLocal()
        try:
            create_or_update_job(
                db=db,
                user_id=user_id,
                status="error",
                error_message=str(exc),
            )
            print(f"[TRAIN] Error persisted to database")
        finally:
            db.close()

        # Don't re-raise; let the thread exit gracefully
        print(f"[TRAIN] Training thread exiting with error state")
    
    finally:
        # End MLflow run if it was started
        if mlflow_run:
            try:
                mlflow.end_run()
                print(f"[TRAIN] MLflow run ended")
            except Exception as end_err:
                print(f"[TRAIN] ⚠️  MLflow end_run error: {str(end_err)}")
