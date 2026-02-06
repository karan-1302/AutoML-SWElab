# lab8/backend/bll/user_history_bll.py
# ─────────────────────────────────────────────────────────────
# User History Business Logic Layer
#
# Provides business logic for user dataset, model, and prediction
# history endpoints.
# ─────────────────────────────────────────────────────────────

from typing import List, Optional
from sqlalchemy.orm import Session

from dal.repositories.dataset_repository import get_datasets_with_columns
from dal.repositories.training_job_repository import get_models_by_dataset
from dal.repositories.prediction_repository import get_predictions_with_metadata


def get_user_datasets(user_id: str, db: Session) -> List[dict]:
    """
    Get all datasets uploaded by a user.
    
    Parameters
    ----------
    user_id : str
        The user ID.
    db : Session
        Database session.
    
    Returns
    -------
    List[dict]
        List of datasets with metadata.
    """
    datasets = get_datasets_with_columns(db, user_id)
    
    if not datasets:
        return []
    
    return datasets


def get_user_dataset_models(user_id: str, dataset_id: str, db: Session) -> List[dict]:
    """
    Get all models trained on a specific dataset by a user.
    
    Parameters
    ----------
    user_id : str
        The user ID.
    dataset_id : str
        The dataset ID.
    db : Session
        Database session.
    
    Returns
    -------
    List[dict]
        List of models with metadata.
    """
    models = get_models_by_dataset(db, user_id, dataset_id)
    
    if not models:
        return []
    
    return models


def get_user_predictions(user_id: str, db: Session) -> List[dict]:
    """
    Get all predictions made by a user.
    
    Parameters
    ----------
    user_id : str
        The user ID.
    db : Session
        Database session.
    
    Returns
    -------
    List[dict]
        List of predictions with metadata.
    """
    predictions = get_predictions_with_metadata(db, user_id)
    
    if not predictions:
        return []
    
    return predictions
