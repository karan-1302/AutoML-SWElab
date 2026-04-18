# lab8/backend/tests/test_whitebox.py
# ─────────────────────────────────────────────────────────────
# White Box Testing
#
# Tests internal structure, code, and logic.
# Covers:
#   - DAL repositories (CRUD operations directly on the DB session)
#   - BLL validation logic (internal functions)
#   - Security utilities
# ─────────────────────────────────────────────────────────────

import pytest
import pandas as pd
from sqlalchemy.exc import IntegrityError

from dal.db_models import User, Dataset
from dal.repositories.user_repository import create_user, get_user_by_email, delete_user
from dal.repositories.dataset_repository import create_dataset
from bll.auth_bll import _validate_credentials
from bll.ingest_bll import _validate_dataframe, _compute_quality_report
from utils.security import hash_password, verify_password


# ── 1. DAL Repository Tests (Internal DB operations) ─────────

def test_user_repository_crud(test_db):
    """Test user creation, retrieval, and deletion in isolation."""
    # Create
    user = create_user(
        db=test_db,
        user_id="test-123",
        email="test@example.com",
        name="Test Agent",
        hashed_password="hashed_pw_xyz"
    )
    assert user.id is not None
    assert user.email == "test@example.com"

    # Retrieve
    fetched = get_user_by_email(test_db, "test@example.com")
    assert fetched is not None
    assert fetched.user_id == "test-123"

    # Delete
    deleted = delete_user(test_db, "test-123")
    assert deleted is True

    # Verify deletion
    fetched_again = get_user_by_email(test_db, "test@example.com")
    assert fetched_again is None


def test_database_unique_constraints(test_db):
    """Test that the database enforces unique constraints (Email/UserID)."""
    create_user(
        db=test_db,
        user_id="user-1",
        email="unique@test.com",
        name="Agent 1",
        hashed_password="pw"
    )

    with pytest.raises(IntegrityError):
        # Attempt to create another user with the same email
        create_user(
            db=test_db,
            user_id="user-2",
            email="unique@test.com",
            name="Agent 2",
            hashed_password="pw"
        )


# ── 2. BLL Validation Logic Tests ────────────────────────────

def test_auth_validation_logic():
    """Test internal credential validation branches."""
    # Valid
    errors = _validate_credentials("user@domain.com", "password123")
    assert len(errors) == 0

    # Missing email
    errors = _validate_credentials("", "password123")
    assert "Email address is required." in errors

    # Invalid email format
    errors = _validate_credentials("invalid_email", "password123")
    assert "Email address is not in a valid format" in errors[0]

    # Short password
    errors = _validate_credentials("user@domain.com", "123")
    assert "Password must be at least 6 characters." in errors[0]


def test_dataframe_validation_logic():
    """Test internal pandas DataFrame validation logic."""
    # Empty DataFrame
    df_empty = pd.DataFrame()
    errors = _validate_dataframe(df_empty)
    assert "The uploaded CSV file is empty" in errors[0]

    # Too few rows
    df_small = pd.DataFrame({"col1": [1, 2], "col2": [3, 4]})
    errors = _validate_dataframe(df_small)
    assert "Dataset must have at least 10 rows for ML training" in errors[0]

    # Too few columns
    df_1col = pd.DataFrame({"col1": list(range(12))})
    errors = _validate_dataframe(df_1col)
    assert "Dataset must have at least 2 columns" in errors[0]

    # Valid
    df_valid = pd.DataFrame({"col1": list(range(12)), "col2": list(range(12))})
    errors = _validate_dataframe(df_valid)
    assert len(errors) == 0


# ── 3. Internal Calculation / Transformation Tests ───────────

def test_quality_report_calculation():
    """Test the internal data quality scoring algorithm."""
    df = pd.DataFrame({
        "num_col": [1, 2, None, 4, 5, 6, 7, 8, 9, 10],  # 1 missing
        "cat_col": ["a", "b", "c", "d", "e", "f", "g", "h", "i", "a"]  # 1 duplicate row if considering just this col, but combined it's unique
    })
    # Since dataset is < 100 rows, it will face a -10 penalty.
    # Missing cells: 1 out of 20 = 5%. Penalty = -5.
    # Base score = 100. Expected around 85.

    report = _compute_quality_report(df)
    
    assert report["total_rows"] == 10
    assert report["missing_cells"] == 1
    assert "num_col" in report["numeric_columns"]
    assert "cat_col" in report["categorical_columns"]
    assert report["quality_score"] == 85.0


# ── 4. Security Utility Tests ────────────────────────────────

def test_password_hashing():
    """Test that password hashing and verification works internally."""
    plain = "my_secret_password"
    hashed = hash_password(plain)
    
    assert hashed != plain
    assert verify_password(plain, hashed) is True
    assert verify_password("wrong_password", hashed) is False
