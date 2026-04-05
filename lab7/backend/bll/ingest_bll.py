# lab7/backend/bll/ingest_bll.py
# ─────────────────────────────────────────────────────────────
# Data Ingestion Business Logic Layer
#
# Business Rules Implemented:
#   BR-ING-01  Only .csv files are accepted.
#   BR-ING-02  File size must not exceed 50 MB.
#   BR-ING-03  CSV must be parseable by pandas.
#   BR-ING-04  Dataset must not be empty (0 rows).
#   BR-ING-05  Dataset must have at least 2 columns.
#   BR-ING-06  Dataset must have at least 10 rows to be usable for ML.
#   BR-ING-07  Data quality report is computed (missing %, duplicate rows, type breakdown).
#   BR-ING-08  Preview is limited to first 10 rows.
#   BR-ING-09  NaN values are replaced with None for JSON serialization.
#
# Data Transformation:
#   DT-ING-01  Raw CSV bytes → pandas DataFrame (tabular structure).
#   DT-ING-02  DataFrame preview → list[dict] JSON-safe format.
#   DT-ING-03  Column types detected and classified (numeric vs categorical).
# ─────────────────────────────────────────────────────────────

import io
import uuid
from typing import Tuple

import pandas as pd

from utils.store import DATASETS

PREVIEW_ROWS   = 10
MAX_FILE_MB    = 50
ALLOWED_SUFFIX = ".csv"
MIN_ROWS       = 10
MIN_COLUMNS    = 2


# ── Validation ────────────────────────────────────────────────

def _validate_file(filename: str, file_bytes: bytes) -> list[str]:
    """Validate the uploaded file before parsing."""
    errors: list[str] = []

    # BR-ING-01: Extension check
    if not filename.lower().endswith(ALLOWED_SUFFIX):
        errors.append(f"Only {ALLOWED_SUFFIX} files are accepted. Got: '{filename}'")

    # BR-ING-02: Size check
    size_mb = len(file_bytes) / (1024 * 1024)
    if size_mb > MAX_FILE_MB:
        errors.append(f"File size ({size_mb:.1f} MB) exceeds the {MAX_FILE_MB} MB limit.")

    return errors


def _validate_dataframe(df: pd.DataFrame) -> list[str]:
    """Validate the parsed DataFrame against business rules."""
    errors: list[str] = []

    # BR-ING-04
    if df.empty or len(df) == 0:
        errors.append("The uploaded CSV file is empty (0 rows).")
        return errors

    # BR-ING-05
    if len(df.columns) < MIN_COLUMNS:
        errors.append(f"Dataset must have at least {MIN_COLUMNS} columns. Found: {len(df.columns)}.")

    # BR-ING-06
    if len(df) < MIN_ROWS:
        errors.append(f"Dataset must have at least {MIN_ROWS} rows for ML training. Found: {len(df)}.")

    return errors


# ── Data Quality Analysis (BR-ING-07) ────────────────────────

def _compute_quality_report(df: pd.DataFrame) -> dict:
    """Generate a data quality report for the uploaded dataset."""
    total_cells      = df.shape[0] * df.shape[1]
    missing_cells    = int(df.isnull().sum().sum())
    missing_pct      = round((missing_cells / total_cells) * 100, 2) if total_cells > 0 else 0
    duplicate_rows   = int(df.duplicated().sum())
    numeric_cols     = df.select_dtypes(include=["int64", "float64"]).columns.tolist()
    categorical_cols = df.select_dtypes(include=["object", "category"]).columns.tolist()

    # Per-column missing info
    column_quality = {}
    for col in df.columns:
        col_missing = int(df[col].isnull().sum())
        col_missing_pct = round((col_missing / len(df)) * 100, 2) if len(df) > 0 else 0
        col_dtype = str(df[col].dtype)
        column_quality[col] = {
            "dtype":       col_dtype,
            "missing":     col_missing,
            "missing_pct": col_missing_pct,
            "unique":      int(df[col].nunique()),
        }

    # Overall quality score (0-100)
    # Deduct for: missing data, duplicates, too few rows
    score = 100
    score -= min(missing_pct, 40)                       # up to -40 for missing data
    dup_pct = (duplicate_rows / len(df)) * 100 if len(df) > 0 else 0
    score -= min(dup_pct / 2, 20)                       # up to -20 for duplicates
    if len(df) < 100:
        score -= 10                                      # penalty for small dataset
    score = max(0, round(score, 1))

    return {
        "total_rows":      len(df),
        "total_columns":   len(df.columns),
        "missing_cells":   missing_cells,
        "missing_pct":     missing_pct,
        "duplicate_rows":  duplicate_rows,
        "numeric_columns": numeric_cols,
        "categorical_columns": categorical_cols,
        "column_quality":  column_quality,
        "quality_score":   score,
    }


# ── Core BLL function ─────────────────────────────────────────

def validate_and_ingest(
    filename: str,
    file_bytes: bytes,
    user_id: str,
) -> Tuple[bool, dict]:
    """
    Validate and ingest a CSV file upload.

    Returns
    -------
    (success, payload)
        On success: (True, {dataset_id, filename, columns, row_count, preview, quality_report})
        On failure: (False, {errors: [str,...], code: int})
    """
    # ── Step 1: File-level validation ─────────────────────────
    file_errors = _validate_file(filename, file_bytes)
    if file_errors:
        return False, {"errors": file_errors, "code": 400}

    # ── Step 2: Parse CSV (BR-ING-03) ─────────────────────────
    try:
        df = pd.read_csv(io.BytesIO(file_bytes))
    except Exception as exc:
        return False, {"errors": [f"Could not parse CSV: {exc}"], "code": 422}

    # ── Step 3: DataFrame validation ──────────────────────────
    df_errors = _validate_dataframe(df)
    if df_errors:
        return False, {"errors": df_errors, "code": 422}

    # ── Step 4: Data quality report (BR-ING-07) ───────────────
    quality_report = _compute_quality_report(df)

    # ── Step 5: Store in memory ───────────────────────────────
    dataset_id = str(uuid.uuid4())
    DATASETS[dataset_id] = {
        "dataset_id":  dataset_id,
        "filename":    filename,
        "user_id":     user_id,
        "dataframe":   df,
        "row_count":   len(df),
        "columns":     list(df.columns),
    }

    # ── Step 6: Build preview (DT-ING-02, BR-ING-08, BR-ING-09) ─
    preview_df = df.head(PREVIEW_ROWS).where(pd.notnull(df.head(PREVIEW_ROWS)), None)
    preview    = preview_df.to_dict(orient="records")

    return True, {
        "dataset_id":     dataset_id,
        "filename":       filename,
        "columns":        list(df.columns),
        "row_count":      len(df),
        "preview":        preview,
        "quality_report": quality_report,
    }
