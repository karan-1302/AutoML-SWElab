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
    file_path: str = None,
    quality_score: float = None,
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
    file_path : str, optional
        Absolute path to the saved CSV file on disk.
    quality_score : float, optional
        Data quality score (0-100).

    Returns
    -------
    Dataset
        The newly created record.
    """
    dataset = Dataset(
        dataset_id=dataset_id,
        filename=filename,
        user_id=user_id,
        column_count=len(columns),
        row_count=row_count,
        file_path=file_path,
        quality_score=quality_score,
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
    """
    Get the list of columns for a dataset.
    
    Note: The actual column names are not stored in the database.
    This returns an empty list. Column names should be retrieved
    from the cached DataFrame or by re-reading the CSV file.
    """
    # Column names are not stored in Supabase schema
    # They are kept in the runtime cache (utils/store.py)
    return []


def get_datasets_with_columns(db: Session, user_id: str) -> List[dict]:
    """
    Retrieve all datasets for a user with additional metadata.
    
    Returns a list of dictionaries with dataset info and column names.
    Column names are retrieved from the runtime cache.
    """
    from utils.store import get_cached_dataset
    
    datasets = db.query(Dataset).filter(Dataset.user_id == user_id).all()
    
    result = []
    for dataset in datasets:
        cached = get_cached_dataset(dataset.dataset_id)
        columns = cached.get("columns", []) if cached else []
        
        result.append({
            "dataset_id": dataset.dataset_id,
            "filename": dataset.filename,
            "row_count": dataset.row_count,
            "column_count": dataset.column_count,
            "quality_score": dataset.quality_score,
            "uploaded_at": dataset.uploaded_at.isoformat() if dataset.uploaded_at else None,
            "columns": columns,
        })
    
    return result


def get_dataset_by_filename_and_user(db: Session, user_id: str, filename: str) -> Optional[Dataset]:
    """
    Retrieve a dataset by filename and user_id.
    
    Returns the dataset if found, None otherwise.
    """
    return db.query(Dataset).filter(
        Dataset.user_id == user_id,
        Dataset.filename == filename
    ).first()
