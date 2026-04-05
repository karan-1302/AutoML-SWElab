# lab8/backend/tests/test_blackbox.py
# ─────────────────────────────────────────────────────────────
# Black Box Testing
#
# Tests application functionality from the outside (HTTP endpoints),
# without knowledge of internal code paths.
# Covers:
#   - Auth router (Login)
#   - Ingest router (Upload)
#   - Error handling (Invalid inputs via API)
# ─────────────────────────────────────────────────────────────

import io
import pytest

# Note: We rely on the `client` and `auth_headers` fixtures from conftest.py
# which provide an isolated TestClient and a seeded database.


# ── 1. Auth Endpoint Tests ────────────────────────────────────

def test_login_success(client):
    """Test authenticating a valid user via the API."""
    response = client.post(
        "/api/auth/login",
        json={"email": "demo@realestate.com", "password": "password123"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["user"]["email"] == "demo@realestate.com"


def test_login_failure_wrong_password(client):
    """Test API response for invalid credentials."""
    response = client.post(
        "/api/auth/login",
        json={"email": "demo@realestate.com", "password": "wrongpassword"}
    )
    assert response.status_code == 401
    assert "Incorrect email or password" in response.json()["detail"][0]


# ── 2. Ingest Endpoint Tests ──────────────────────────────────

def test_upload_csv_success(client, auth_headers):
    """Test uploading a valid CSV dataset via the API."""
    csv_content = b"price,bedrooms,bathrooms\n" + b"500000,3,2\n600000,4,3\n" * 10
    file_tuple = ("test_data.csv", io.BytesIO(csv_content), "text/csv")
    
    response = client.post(
        "/api/ingest/upload",
        headers=auth_headers,
        files={"file": file_tuple}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "dataset_id" in data
    assert data["row_count"] == 20
    assert "price" in data["columns"]


def test_upload_invalid_file_type(client, auth_headers):
    """Test API validation for non-CSV files."""
    text_content = b"This is just some text, not a CSV."
    file_tuple = ("test_data.txt", io.BytesIO(text_content), "text/plain")
    
    response = client.post(
        "/api/ingest/upload",
        headers=auth_headers,
        files={"file": file_tuple}
    )
    
    assert response.status_code == 400
    assert "Only .csv files are accepted" in response.json()["detail"][0]


# ── 3. Train & Predict Endpoints (Validation / Error paths) ──

def test_start_training_missing_dataset(client, auth_headers):
    """Test starting AutoML with a non-existent dataset via API."""
    response = client.post(
        "/api/train/start",
        headers=auth_headers,
        json={"dataset_id": "invalid-id", "target_column": "price"}
    )
    
    assert response.status_code == 404
    assert "not found" in response.json()["detail"][0]


def test_predict_without_auth(client):
    """Test prediction endpoint enforces authentication."""
    # Notice we do NOT pass auth_headers here
    response = client.post(
        "/api/predict",
        json={
            "bedrooms": 3, "bathrooms": 2, "sqft_living": 1500, "sqft_lot": 5000,
            "floors": 1, "waterfront": 0, "view": 0, "condition": 3, "grade": 7,
            "yr_built": 1990, "zipcode": "98000"
        }
    )
    
    # 401 Unauthorized expected
    assert response.status_code == 401
