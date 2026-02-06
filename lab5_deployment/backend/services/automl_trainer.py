# backend/services/automl_trainer.py
# ─────────────────────────────────────────────────────────────
# KEY MODULE 1: AutoML Trainer  (Layer 3 — Business Logic Layer)
# ─────────────────────────────────────────────────────────────
#
# Implements the BLL component "AutoMLTrainer" from Lab 4 Section III:
#   - trainAll(dataset)      → trains LinearRegression, RandomForest, XGBoost
#   - evaluateModels(metric) → scores each model on the held-out test set
#   - selectBestModel()      → picks the winner by R²
#
# Maps to DFD Process 3.0: "AutoML Training & Registry"
#   Input:  cleaned dataset from D2 (Dataset Storage)
#   Output: best trained model saved to D3 (Model Registry / DagsHub MLflow)
#
# In this deployment implementation the model is kept in the in-memory store
# (utils/store.py → TRAINING_JOBS).  To deploy to Render + DagsHub, replace
# the set_training_job() call at the end with an mlflow.log_artifact() call.

import math
import time
import pandas as pd

from sklearn.model_selection import train_test_split
from sklearn.pipeline        import Pipeline
from sklearn.compose         import ColumnTransformer
from sklearn.preprocessing   import StandardScaler, OneHotEncoder
from sklearn.impute          import SimpleImputer
from sklearn.linear_model    import LinearRegression
from sklearn.ensemble        import RandomForestRegressor
from sklearn.metrics         import mean_squared_error, mean_absolute_error, r2_score
from xgboost                 import XGBRegressor

from utils.store import set_training_job, TRAINING_JOBS

# Candidate algorithms (Lab 4 Section III — AutoMLTrainer)
ALGORITHMS = ["LinearRegression", "RandomForest", "XGBoost"]


# ── Preprocessing (DAL helper, called by BLL) ─────────────────
def _build_preprocessor(X: pd.DataFrame) -> ColumnTransformer:
    """
    Build a ColumnTransformer that handles both numeric and categorical columns.

    Numeric  → median imputation → StandardScaler
    Categorical → constant imputation → OneHotEncoder

    This mirrors the preprocessing step in the existing train_model.py but is
    decoupled from Streamlit so it can run inside a FastAPI background task.
    """
    num_cols = X.select_dtypes(include=["int64", "float64"]).columns.tolist()
    cat_cols = X.select_dtypes(include=["object", "category"]).columns.tolist()

    num_pipe = Pipeline([
        ("imputer", SimpleImputer(strategy="median")),
        ("scaler",  StandardScaler()),
    ])
    cat_pipe = Pipeline([
        ("imputer", SimpleImputer(strategy="constant", fill_value="Unknown")),
        ("onehot",  OneHotEncoder(handle_unknown="ignore", sparse_output=False)),
    ])

    transformers = []
    if num_cols:
        transformers.append(("num", num_pipe, num_cols))
    if cat_cols:
        transformers.append(("cat", cat_pipe, cat_cols))

    return ColumnTransformer(transformers=transformers, remainder="drop")


def _compute_metrics(y_true, y_pred) -> dict:
    """Return RMSE, MAE, and R² for a set of predictions."""
    mse = mean_squared_error(y_true, y_pred)
    return {
        "rmse": round(math.sqrt(mse), 4),
        "mae":  round(mean_absolute_error(y_true, y_pred), 4),
        "r2":   round(r2_score(y_true, y_pred), 6),
    }


# ── Main BLL function ─────────────────────────────────────────
def run_automl(user_id: str, df: pd.DataFrame, target_column: str):
    """
    AutoMLTrainer.trainAll() — BLL entry point.

    Runs in a background thread (started by the /api/train/start router).
    Writes incremental progress to the in-memory store so the frontend
    can poll /api/train/status and show a live progress bar.

    Steps
    -----
    1. Validate and split the dataset (80 / 20).
    2. Build a shared preprocessing pipeline.
    3. Train each candidate model, recording progress after each step.
    4. Evaluate all models on the test set.
    5. Select the best model by R² (AutoMLTrainer.selectBestModel).
    6. Persist the winning pipeline to the store (D3 in production → DagsHub).

    Parameters
    ----------
    user_id       : identifies which user's job slot to update in the store
    df            : the full cleaned DataFrame (loaded from D2)
    target_column : the column the model should predict (e.g. "price")
    """

    # ── Step 0: Initialise job state in the store (D3 placeholder) ──
    set_training_job(user_id, {
        "status":          "running",
        "progress":        {algo: 0 for algo in ALGORITHMS},
        "scores":          {},
        "best_model_name": None,
        "pipeline":        None,
        "target_column":   target_column,
        "feature_columns": [],
        "error":           None,
    })

    try:
        # ── Step 1: Validate & split ──────────────────────────
        if target_column not in df.columns:
            raise ValueError(
                f"Target column '{target_column}' not found. "
                f"Available columns: {list(df.columns)}"
            )

        df = df.dropna(subset=[target_column]).copy()
        X  = df.drop(columns=[target_column])
        y  = df[target_column].astype(float)

        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.20, random_state=42
        )
        feature_columns = X.columns.tolist()

        # ── Step 2: Build shared preprocessor ────────────────
        preprocessor = _build_preprocessor(X_train)

        # ── Step 3 & 4: Train + evaluate each candidate ──────
        candidates = {
            "LinearRegression": LinearRegression(),
            "RandomForest":     RandomForestRegressor(
                                    n_estimators=100, random_state=42, n_jobs=-1),
            "XGBoost":          XGBRegressor(
                                    n_estimators=100, random_state=42,
                                    verbosity=0, eval_metric="rmse"),
        }

        trained_pipelines: dict = {}
        all_scores:        dict = {}
        best_r2   = -float("inf")
        best_name = ""

        for name, model in candidates.items():
            # Mark algorithm as started (10 %)
            _update_progress(user_id, name, 10)
            time.sleep(0.3)   # small delay so the frontend poll can visualise it

            pipe = Pipeline([
                ("preprocessor", preprocessor),
                ("model",        model),
            ])

            # Simulate mid-training progress ticks
            _update_progress(user_id, name, 40)
            time.sleep(0.3)
            _update_progress(user_id, name, 70)

            # Fit the full pipeline
            pipe.fit(X_train, y_train)
            y_pred  = pipe.predict(X_test)
            metrics = _compute_metrics(y_test, y_pred)

            trained_pipelines[name] = pipe
            all_scores[name]        = metrics

            # Mark algorithm as complete (100 %)
            _update_progress(user_id, name, 100, score=metrics["r2"])

            # AutoMLTrainer.evaluateModels — track best by R²
            if metrics["r2"] > best_r2:
                best_r2   = metrics["r2"]
                best_name = name

        # ── Step 5 & 6: Persist best model (D3) ──────────────
        # Production: replace set_training_job with mlflow.log_artifact()
        set_training_job(user_id, {
            **TRAINING_JOBS[user_id],
            "status":          "done",
            "best_model_name": best_name,
            "pipeline":        trained_pipelines[best_name],
            "feature_columns": feature_columns,
            "all_scores":      all_scores,
        })

    except Exception as exc:
        # Surface the error so the status endpoint can report it
        current = TRAINING_JOBS.get(user_id, {})
        current["status"] = "error"
        current["error"]  = str(exc)
        set_training_job(user_id, current)
        raise


def _update_progress(user_id: str, algo: str, pct: int, score: float = None):
    """Write a progress tick for one algorithm into the store."""
    job = TRAINING_JOBS.get(user_id, {})
    job["progress"][algo] = pct
    if score is not None:
        job["scores"][algo] = job.get("scores", {}).get(algo, {})
        job["progress"][f"{algo}_score"] = round(score, 4)
    set_training_job(user_id, job)
