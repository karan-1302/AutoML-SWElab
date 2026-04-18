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
    )
    db.add(prediction)
    db.commit()
    db.refresh(prediction)
    return prediction


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


def delete_predictions_by_user(db: Session, user_id: str) -> int:
    """Delete all predictions for a user. Returns count deleted."""
    count = db.query(Prediction).filter(Prediction.user_id == user_id).delete()
    db.commit()
    return count
