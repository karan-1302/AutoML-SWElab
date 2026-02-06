# lab8/backend/dal/repositories/prediction_repository.py
# ─────────────────────────────────────────────────────────────
# Data Access Layer — Prediction Repository
#
# Provides CRUD operations for the `predictions` table.
# Stores prediction metadata in SQLite; the sklearn Pipeline
# used for explainability remains in the in-memory runtime cache.
# ─────────────────────────────────────────────────────────────

import json
from typing import Optional, List
from sqlalchemy.orm import Session

from dal.db_models import Prediction


def save_prediction(
    db: Session,
    user_id: str,
    predicted_price: float,
    model_used: str,
    confidence: float,
    input_features: dict,
    dataset_id: str = None,
    model_name: str = None,
    target_column: str = None,
) -> Prediction:
    """
    Save a prediction result to the database.

    Parameters
    ----------
    db : Session
        Active SQLAlchemy session.
    user_id : str
        The user who made the prediction.
    predicted_price : float
        The model's price prediction.
    model_used : str
        Name of the ML model used.
    confidence : float
        Confidence score (50-99%).
    input_features : dict
        Feature values submitted for prediction.
    dataset_id : str, optional
        The dataset ID associated with the model.
    model_name : str, optional
        The name of the persisted model.
    target_column : str, optional
        The target column used in the model.

    Returns
    -------
    Prediction
        The newly created prediction record.
    """
    prediction = Prediction(
        user_id=user_id,
        predicted_price=predicted_price,
        model_used=model_used,
        confidence=confidence,
        input_features_json=json.dumps(input_features),
        dataset_id=dataset_id,
        model_name=model_name,
        target_column=target_column,
    )
    db.add(prediction)
    db.commit()
    db.refresh(prediction)
    return prediction


def save_prediction_with_metadata(
    db: Session,
    user_id: str,
    predicted_price: float,
    model_used: str,
    confidence: float,
    input_features: dict,
    dataset_id: str,
    model_name: str,
    target_column: str,
) -> Prediction:
    """
    Save a prediction result with full metadata (dataset_id, model_name, target_column).
    
    This is a convenience wrapper for predictions made with persisted models.
    """
    return save_prediction(
        db=db,
        user_id=user_id,
        predicted_price=predicted_price,
        model_used=model_used,
        confidence=confidence,
        input_features=input_features,
        dataset_id=dataset_id,
        model_name=model_name,
        target_column=target_column,
    )


def get_last_prediction(db: Session, user_id: str) -> Optional[Prediction]:
    """
    Retrieve the most recent prediction for a user.

    Returns the latest prediction ordered by created_at descending.
    """
    return (
        db.query(Prediction)
        .filter(Prediction.user_id == user_id)
        .order_by(Prediction.created_at.desc())
        .first()
    )


def get_predictions_by_user(db: Session, user_id: str) -> List[Prediction]:
    """Retrieve all predictions for a user, newest first."""
    return (
        db.query(Prediction)
        .filter(Prediction.user_id == user_id)
        .order_by(Prediction.created_at.desc())
        .all()
    )


def get_input_features(prediction: Prediction) -> dict:
    """Deserialise input_features_json to a Python dict."""
    return json.loads(prediction.input_features_json)


def get_predictions_with_metadata(db: Session, user_id: str) -> List[dict]:
    """
    Retrieve all predictions for a user with full metadata.
    
    Returns a list of dictionaries with prediction info.
    """
    predictions = db.query(Prediction).filter(
        Prediction.user_id == user_id
    ).order_by(Prediction.created_at.desc()).all()
    
    result = []
    for pred in predictions:
        result.append({
            "prediction_id": pred.id,
            "predicted_price": pred.predicted_price,
            "model_used": pred.model_used,
            "confidence": pred.confidence,
            "dataset_id": pred.dataset_id,
            "model_name": pred.model_name,
            "target_column": pred.target_column,
            "input_features": get_input_features(pred),
            "created_at": pred.created_at.isoformat() if pred.created_at else None,
        })
    
    return result


def delete_predictions_by_user(db: Session, user_id: str) -> int:
    """Delete all predictions for a user. Returns count deleted."""
    count = db.query(Prediction).filter(Prediction.user_id == user_id).delete()
    db.commit()
    return count
