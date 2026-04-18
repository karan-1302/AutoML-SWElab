# lab8/backend/dal/repositories/dataset_repository.py
# ─────────────────────────────────────────────────────────────
# Data Access Layer — Dataset Repository
#
# Provides CRUD operations for the `datasets` table.
# Stores dataset metadata in SQLite; the actual pandas DataFrame
# is kept in the in-memory runtime cache for ML operations.
# ─────────────────────────────────────────────────────────────

import json
from typing import Optional, List
from sqlalchemy.orm import Session

from dal.db_models import Dataset


def create_dataset(
    db: Session,
    dataset_id: str,
    filename: str,
    user_id: str,
    columns: list,
    row_count: int,
) -> Dataset:
    """
    Insert a new dataset metadata record.

    Parameters
    ----------
    db : Session
        Active SQLAlchemy session.
    dataset_id : str
        UUID for the dataset.
    filename : str
        Original uploaded filename.
    user_id : str
        Owner's user_id.
    columns : list
        List of column names.
    row_count : int
        Number of rows in the dataset.

    Returns
    -------
    Dataset
        The newly created record.
    """
    dataset = Dataset(
        dataset_id=dataset_id,
        filename=filename,
        user_id=user_id,
        columns_json=json.dumps(columns),
        row_count=row_count,
    )
    db.add(dataset)
    db.commit()
    db.refresh(dataset)
    return dataset


def get_dataset_by_id(db: Session, dataset_id: str) -> Optional[Dataset]:
    """Retrieve a dataset by its unique dataset_id."""
    return db.query(Dataset).filter(Dataset.dataset_id == dataset_id).first()


def get_datasets_by_user(db: Session, user_id: str) -> List[Dataset]:
    """Retrieve all datasets belonging to a user."""
    return db.query(Dataset).filter(Dataset.user_id == user_id).all()


def delete_dataset(db: Session, dataset_id: str) -> bool:
    """
    Delete a dataset by dataset_id.

    Returns True if deleted, False if not found.
    """
    dataset = db.query(Dataset).filter(Dataset.dataset_id == dataset_id).first()
    if dataset:
        db.delete(dataset)
        db.commit()
        return True
    return False


def get_columns(dataset: Dataset) -> list:
    """Deserialise the columns_json field to a Python list."""
    return json.loads(dataset.columns_json)
