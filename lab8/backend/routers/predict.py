# lab8/backend/routers/predict.py
# ─────────────────────────────────────────────────────────────
# Thin Router: Prediction
# Updated for Lab 8: injects database session via DAL.
# ─────────────────────────────────────────────────────────────

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from models.schemas   import PredictRequest, PredictResponse, PredictPersistRequest, PredictPersistResponse
from utils.security   import get_current_user
from bll.predict_bll  import validate_and_predict, validate_and_predict_persist
from dal.database     import get_db

router = APIRouter()


@router.post("", response_model=PredictResponse)
def predict_price(
    body: PredictRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Run a property price prediction.
    Results are persisted to the database via DAL.
    """
    features = body.model_dump()

    success, result = validate_and_predict(
        features=features,
        user_id=current_user["user_id"],
        db=db,
    )

    if not success:
        raise HTTPException(
            status_code=result.get("code", 400),
            detail=result["errors"],
        )

    return PredictResponse(**result)


@router.post("/persist", response_model=PredictPersistResponse)
def predict_with_persisted_model(
    body: PredictPersistRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Run a prediction using a persisted model loaded from disk.
    Loads the model from models_storage/{user_id}/{dataset_id}/{target_column}/{model_name}.pkl
    Results are persisted to the database with full metadata.
    """
    success, result = validate_and_predict_persist(
        dataset_id=body.dataset_id,
        target_column=body.target_column,
        model_name=body.model_name,
        features=body.features,
        user_id=current_user["user_id"],
        db=db,
    )

    if not success:
        raise HTTPException(
            status_code=result.get("code", 400),
            detail=result["errors"],
        )

    return PredictPersistResponse(**result)


@router.post("/smart", response_model=PredictPersistResponse)
def predict_with_smart_defaults(
    body: PredictPersistRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Feature 4: Smart prediction with auto-fill default values.
    User provides only the fields they want to specify.
    All other fields are filled with dataset column averages.
    
    The body.features dict contains only the user-specified values.
    Missing fields are auto-filled with averages from the cached dataset.
    """
    from utils.store import get_cached_dataset
    import pandas as pd
    
    # Get cached dataset to compute averages
    cached_dataset = get_cached_dataset(body.dataset_id)
    
    if not cached_dataset or "dataframe" not in cached_dataset:
        raise HTTPException(
            status_code=404,
            detail=["Dataset not found in cache. Please re-upload the dataset."],
        )
    
    df = cached_dataset["dataframe"]
    
    # Compute column means for numeric columns
    numeric_cols = df.select_dtypes(include=['number']).columns
    column_means = df[numeric_cols].mean().to_dict()
    
    # Fill missing features with averages
    complete_features = body.features.copy()
    
    # Get all feature columns from the model
    import json
    from pathlib import Path
    model_dir = Path("models_storage") / current_user["user_id"] / body.dataset_id / body.target_column
    info_path = model_dir / "model_info.json"
    
    if info_path.exists():
        with open(info_path, "r") as f:
            model_info = json.load(f)
        feature_columns = model_info.get("feature_columns", [])
        
        # Fill missing columns with averages
        for col in feature_columns:
            if col not in complete_features:
                if col in column_means:
                    complete_features[col] = column_means[col]
                else:
                    # For non-numeric columns (like zipcode), use mode or default
                    if col in df.columns:
                        complete_features[col] = df[col].mode()[0] if len(df[col].mode()) > 0 else df[col].iloc[0]
    
    # Now call the regular persist prediction with complete features
    success, result = validate_and_predict_persist(
        dataset_id=body.dataset_id,
        target_column=body.target_column,
        model_name=body.model_name,
        features=complete_features,
        user_id=current_user["user_id"],
        db=db,
    )
    
    if not success:
        raise HTTPException(
            status_code=result.get("code", 400),
            detail=result["errors"],
        )
    
    return PredictPersistResponse(**result)
