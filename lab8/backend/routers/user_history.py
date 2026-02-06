# lab8/backend/routers/user_history.py
# ─────────────────────────────────────────────────────────────
# Thin Router: User History Endpoints
#
# Provides endpoints for users to view their:
# - Uploaded datasets
# - Trained models
# - Made predictions
# ─────────────────────────────────────────────────────────────

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from models.schemas import DatasetInfo, ModelInfo, PredictionInfo
from utils.security import get_current_user
from bll.user_history_bll import (
    get_user_datasets,
    get_user_dataset_models,
    get_user_predictions,
)
from dal.database import get_db

router = APIRouter()


@router.get("/datasets", response_model=list[DatasetInfo])
def get_user_datasets_endpoint(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get all datasets uploaded by the authenticated user.
    
    Returns a list of datasets with metadata including:
    - dataset_id, filename, row_count, column_count
    - quality_score, uploaded_at, column names
    
    Returns an empty list if the user has no datasets.
    """
    datasets = get_user_datasets(current_user["user_id"], db)
    
    # Return empty list if no datasets (not 404)
    return datasets


@router.get("/datasets/{dataset_id}/models", response_model=list[ModelInfo])
def get_user_dataset_models_endpoint(
    dataset_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get all models trained on a specific dataset by the authenticated user.
    
    Returns a list of models with metadata including:
    - model_name, target_column, scores, trained_at
    - status, feature_columns
    
    Returns an empty list if no models exist for the dataset.
    """
    models = get_user_dataset_models(current_user["user_id"], dataset_id, db)
    
    # Return empty list if no models (not 404)
    return models


@router.get("/predictions", response_model=list[PredictionInfo])
def get_user_predictions_endpoint(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get all predictions made by the authenticated user.
    
    Returns a list of predictions with metadata including:
    - predicted_price, model_used, confidence
    - dataset_id, model_name, target_column
    - input_features, created_at
    
    Returns an empty list if the user has no predictions.
    """
    predictions = get_user_predictions(current_user["user_id"], db)
    
    # Return empty list if no predictions (not 404)
    return predictions


@router.get("/datasets/{dataset_id}/stats")
def get_dataset_stats_endpoint(
    dataset_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Feature 4: Get column statistics (mean, min, max) for a dataset.
    Used for smart prediction with auto-fill default values.
    
    Returns statistics for all numeric columns in the dataset.
    """
    from utils.store import get_cached_dataset, cache_dataset
    from dal.repositories.dataset_repository import get_dataset_by_id
    import pandas as pd
    import os
    
    # Get cached dataset
    cached_dataset = get_cached_dataset(dataset_id)
    
    if not cached_dataset or "dataframe" not in cached_dataset:
        # Try to load from database and file system
        db_dataset = get_dataset_by_id(db, dataset_id)
        if not db_dataset:
            raise HTTPException(
                status_code=404,
                detail="Dataset not found in database.",
            )
        
        # Check if file exists on disk
        if not db_dataset.file_path or not os.path.exists(db_dataset.file_path):
            raise HTTPException(
                status_code=404,
                detail="Dataset file not found on disk. Please re-upload the dataset.",
            )
        
        # Load CSV from disk
        try:
            df = pd.read_csv(db_dataset.file_path)
            columns = list(df.columns)
            
            # Cache the dataset for future use
            cache_dataset(dataset_id, {
                "dataset_id":  dataset_id,
                "filename":    db_dataset.filename,
                "user_id":     current_user["user_id"],
                "dataframe":   df,
                "row_count":   len(df),
                "columns":     columns,
            })
            
            cached_dataset = get_cached_dataset(dataset_id)
            print(f"[user_history] Loaded dataset {dataset_id} from disk and cached it")
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to load dataset from disk: {str(e)}",
            )
    
    df = cached_dataset["dataframe"]
    
    # Compute statistics for numeric columns
    numeric_cols = df.select_dtypes(include=['number']).columns
    stats = {}
    
    for col in numeric_cols:
        stats[col] = {
            "mean": float(df[col].mean()),
            "min": float(df[col].min()),
            "max": float(df[col].max()),
            "median": float(df[col].median()),
        }
    
    # For non-numeric columns, provide mode
    non_numeric_cols = df.select_dtypes(exclude=['number']).columns
    for col in non_numeric_cols:
        mode_val = df[col].mode()[0] if len(df[col].mode()) > 0 else df[col].iloc[0]
        stats[col] = {
            "mode": str(mode_val),
            "unique_count": int(df[col].nunique()),
        }
    
    return stats
