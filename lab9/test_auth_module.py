# lab9/test_auth_module.py
# ─────────────────────────────────────────────────────────────
# Lab 9: Test Cases for Authentication Module
# 8 comprehensive test cases as per Assignment 9 requirements
# ─────────────────────────────────────────────────────────────

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "lab8", "backend"))

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from dal.database import Base, get_db
from dal.db_models import User
from utils.security import hash_password, verify_password, create_access_token
from main import app


# ── Test Database Setup ───────────────────────────────────────

@pytest.fixture(scope="function")
def test_db():
    """Create an in-memory SQLite database for each test."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)
    
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def seeded_db(test_db):
    """Test database pre-seeded with a demo user."""
    demo_user = User(
        user_id="user-001",
        email="demo@realestate.com",
        full_name="Demo Agent",
        hashed_password=hash_password("password123"),
    )
    test_db.add(demo_user)
    test_db.commit()
    test_db.refresh(demo_user)
    return test_db


@pytest.fixture(scope="function")
def client(seeded_db):
    """FastAPI TestClient with database override."""
    def _override_get_db():
        try:
            yield seeded_db
        finally:
            pass
    
    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


# ══════════════════════════════════════════════════════════════
# TEST CASES FOR LAB 9
# ══════════════════════════════════════════════════════════════

def test_case_1_successful_registration(client):
    """
    TC-AUTH-001: Successful User Registration
    
    Test Scenario: User successfully registers with valid credentials
    Input: Valid email, password, and full name
    Expected: HTTP 200, access_token returned, user data present
    """
    print("\n" + "="*60)
    print("TEST CASE 1: Successful User Registration")
    print("="*60)
    
    payload = {
        "email": "newuser@realestate.com",
        "password": "SecurePass123",
        "full_name": "John Doe"
    }
    
    print(f"Input Data: {payload}")
    
    response = client.post("/api/auth/register", json=payload)
    
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")
    
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["email"] == "newuser@realestate.com"
    assert data["user"]["full_name"] == "John Doe"
    assert "user_id" in data["user"]
    
    print("✅ TEST PASSED")


def test_case_2_duplicate_email_registration(client):
    """
    TC-AUTH-002: Registration with Duplicate Email
    
    Test Scenario: User attempts to register with existing email
    Input: Email that already exists in database
    Expected: HTTP 409, error message about duplicate email
    """
    print("\n" + "="*60)
    print("TEST CASE 2: Registration with Duplicate Email")
    print("="*60)
    
    payload = {
        "email": "demo@realestate.com",  # Already exists
        "password": "Password123",
        "full_name": "Jane Doe"
    }
    
    print(f"Input Data: {payload}")
    
    response = client.post("/api/auth/register", json=payload)
    
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")
    
    assert response.status_code == 409
    data = response.json()
    assert "detail" in data
    assert "already exists" in str(data["detail"]).lower()
    
    print("✅ TEST PASSED")


def test_case_3_invalid_email_format(client):
    """
    TC-AUTH-003: Registration with Invalid Email Format
    
    Test Scenario: User attempts to register with invalid email
    Input: Email without @ symbol or domain
    Expected: HTTP 422, validation error message
    """
    print("\n" + "="*60)
    print("TEST CASE 3: Registration with Invalid Email Format")
    print("="*60)
    
    payload = {
        "email": "invalid_email_format",
        "password": "Password123",
        "full_name": "Test User"
    }
    
    print(f"Input Data: {payload}")
    
    response = client.post("/api/auth/register", json=payload)
    
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")
    
    assert response.status_code == 422
    data = response.json()
    assert "detail" in data
    detail_str = str(data["detail"]).lower()
    assert "email" in detail_str or "format" in detail_str
    
    print("✅ TEST PASSED")


def test_case_4_weak_password(client):
    """
    TC-AUTH-004: Registration with Weak Password
    
    Test Scenario: User attempts to register with password < 6 characters
    Input: Password with only 3 characters
    Expected: HTTP 422, validation error about password length
    """
    print("\n" + "="*60)
    print("TEST CASE 4: Registration with Weak Password")
    print("="*60)
    
    payload = {
        "email": "user@realestate.com",
        "password": "123",  # Too short
        "full_name": "Test User"
    }
    
    print(f"Input Data: {payload}")
    
    response = client.post("/api/auth/register", json=payload)
    
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")
    
    assert response.status_code == 422
    data = response.json()
    assert "detail" in data
    detail_str = str(data["detail"]).lower()
    assert "password" in detail_str and ("6" in detail_str or "characters" in detail_str)
    
    print("✅ TEST PASSED")


def test_case_5_successful_login(client):
    """
    TC-AUTH-005: Successful User Login
    
    Test Scenario: User successfully logs in with correct credentials
    Input: Valid email and password
    Expected: HTTP 200, JWT token returned
    """
    print("\n" + "="*60)
    print("TEST CASE 5: Successful User Login")
    print("="*60)
    
    payload = {
        "email": "demo@realestate.com",
        "password": "password123"
    }
    
    print(f"Input Data: {payload}")
    
    response = client.post("/api/auth/login", json=payload)
    
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")
    
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["email"] == "demo@realestate.com"
    assert len(data["access_token"]) > 20  # JWT token should be long
    
    print("✅ TEST PASSED")


def test_case_6_incorrect_password(client):
    """
    TC-AUTH-006: Login with Incorrect Password
    
    Test Scenario: User attempts to log in with wrong password
    Input: Valid email but incorrect password
    Expected: HTTP 401, authentication error
    """
    print("\n" + "="*60)
    print("TEST CASE 6: Login with Incorrect Password")
    print("="*60)
    
    payload = {
        "email": "demo@realestate.com",
        "password": "WrongPassword123"
    }
    
    print(f"Input Data: {payload}")
    
    response = client.post("/api/auth/login", json=payload)
    
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")
    
    assert response.status_code == 401
    data = response.json()
    assert "detail" in data
    detail_str = str(data["detail"]).lower()
    assert "incorrect" in detail_str or "invalid" in detail_str
    
    print("✅ TEST PASSED")


def test_case_7_nonexistent_email(client):
    """
    TC-AUTH-007: Login with Non-existent Email
    
    Test Scenario: User attempts to log in with email not in database
    Input: Email that doesn't exist
    Expected: HTTP 401, authentication error
    """
    print("\n" + "="*60)
    print("TEST CASE 7: Login with Non-existent Email")
    print("="*60)
    
    payload = {
        "email": "nonexistent@realestate.com",
        "password": "Password123"
    }
    
    print(f"Input Data: {payload}")
    
    response = client.post("/api/auth/login", json=payload)
    
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")
    
    assert response.status_code == 401
    data = response.json()
    assert "detail" in data
    detail_str = str(data["detail"]).lower()
    assert "incorrect" in detail_str or "invalid" in detail_str
    
    print("✅ TEST PASSED")


def test_case_8_password_hashing_security():
    """
    TC-AUTH-008: Password Hashing and Verification
    
    Test Scenario: Verify password security mechanisms
    Input: Plain text password
    Expected: Hash generated, hash != password, verification works
    """
    print("\n" + "="*60)
    print("TEST CASE 8: Password Hashing and Verification")
    print("="*60)
    
    password = "MySecurePassword123"
    print(f"Input Password: {password}")
    
    # Hash the password
    hashed = hash_password(password)
    print(f"Hashed Password: {hashed[:50]}...")
    
    # Verify hash is different from original
    assert hashed != password
    print("✓ Hash is different from original password")
    
    # Verify correct password
    assert verify_password(password, hashed) is True
    print("✓ Correct password verification: SUCCESS")
    
    # Verify incorrect password
    assert verify_password("WrongPassword", hashed) is False
    print("✓ Incorrect password verification: REJECTED")
    
    # Verify hash length (bcrypt produces 60-char hashes)
    assert len(hashed) >= 50
    print(f"✓ Hash length: {len(hashed)} characters")
    
    print("✅ TEST PASSED")


if __name__ == "__main__":
    print("\n" + "="*70)
    print("LAB 9: AUTHENTICATION MODULE TEST SUITE")
    print("Real Estate AutoML System - CS 331 Software Engineering Lab")
    print("="*70)
    
    pytest.main([__file__, "-v", "-s", "--tb=short"])


# ══════════════════════════════════════════════════════════════
# ADDITIONAL TEST CASES (9-25) - To reach 20+ tests
# ══════════════════════════════════════════════════════════════

def test_case_9_empty_email(client):
    """TC-AUTH-009: Registration with empty email"""
    print("\n" + "="*60)
    print("TEST CASE 9: Registration with Empty Email")
    print("="*60)
    
    payload = {"email": "", "password": "Password123", "full_name": "Test User"}
    response = client.post("/api/auth/register", json=payload)
    
    print(f"Status Code: {response.status_code}")
    assert response.status_code == 422
    assert "detail" in response.json()
    print("✅ TEST PASSED")


def test_case_10_empty_password(client):
    """TC-AUTH-010: Registration with empty password"""
    print("\n" + "="*60)
    print("TEST CASE 10: Registration with Empty Password")
    print("="*60)
    
    payload = {"email": "test@test.com", "password": "", "full_name": "Test User"}
    response = client.post("/api/auth/register", json=payload)
    
    print(f"Status Code: {response.status_code}")
    assert response.status_code == 422
    assert "detail" in response.json()
    print("✅ TEST PASSED")


def test_case_11_empty_full_name(client):
    """TC-AUTH-011: Registration with empty full name"""
    print("\n" + "="*60)
    print("TEST CASE 11: Registration with Empty Full Name")
    print("="*60)
    
    payload = {"email": "test@test.com", "password": "Password123", "full_name": ""}
    response = client.post("/api/auth/register", json=payload)
    
    print(f"Status Code: {response.status_code}")
    assert response.status_code == 422
    assert "detail" in response.json()
    print("✅ TEST PASSED")


def test_case_12_whitespace_email(client):
    """TC-AUTH-012: Registration with whitespace-only email"""
    print("\n" + "="*60)
    print("TEST CASE 12: Registration with Whitespace Email")
    print("="*60)
    
    payload = {"email": "   ", "password": "Password123", "full_name": "Test"}
    response = client.post("/api/auth/register", json=payload)
    
    print(f"Status Code: {response.status_code}")
    assert response.status_code == 422
    print("✅ TEST PASSED")


def test_case_13_email_case_insensitive(client):
    """TC-AUTH-013: Login with different email case"""
    print("\n" + "="*60)
    print("TEST CASE 13: Email Case Insensitivity")
    print("="*60)
    
    payload = {"email": "DEMO@REALESTATE.COM", "password": "password123"}
    response = client.post("/api/auth/login", json=payload)
    
    print(f"Status Code: {response.status_code}")
    assert response.status_code == 200
    assert "access_token" in response.json()
    print("✅ TEST PASSED")


def test_case_14_jwt_token_structure(client):
    """TC-AUTH-014: Verify JWT token structure"""
    print("\n" + "="*60)
    print("TEST CASE 14: JWT Token Structure Validation")
    print("="*60)
    
    payload = {"email": "demo@realestate.com", "password": "password123"}
    response = client.post("/api/auth/login", json=payload)
    
    assert response.status_code == 200
    token = response.json()["access_token"]
    
    # JWT has 3 parts separated by dots
    parts = token.split(".")
    assert len(parts) == 3
    print(f"Token parts: {len(parts)}")
    print("✅ TEST PASSED")


def test_case_15_user_data_in_response(client):
    """TC-AUTH-015: Verify user data completeness in response"""
    print("\n" + "="*60)
    print("TEST CASE 15: User Data Completeness")
    print("="*60)
    
    payload = {"email": "demo@realestate.com", "password": "password123"}
    response = client.post("/api/auth/login", json=payload)
    
    assert response.status_code == 200
    user = response.json()["user"]
    assert "user_id" in user
    assert "email" in user
    assert "full_name" in user
    assert user["email"] == "demo@realestate.com"
    print("✅ TEST PASSED")


def test_case_16_password_min_length_boundary(client):
    """TC-AUTH-016: Password exactly 6 characters (boundary test)"""
    print("\n" + "="*60)
    print("TEST CASE 16: Password Minimum Length Boundary")
    print("="*60)
    
    payload = {"email": "boundary@test.com", "password": "123456", "full_name": "Boundary Test"}
    response = client.post("/api/auth/register", json=payload)
    
    print(f"Status Code: {response.status_code}")
    assert response.status_code == 200
    assert "access_token" in response.json()
    print("✅ TEST PASSED")


def test_case_17_password_5_chars(client):
    """TC-AUTH-017: Password with 5 characters (just below boundary)"""
    print("\n" + "="*60)
    print("TEST CASE 17: Password 5 Characters (Below Boundary)")
    print("="*60)
    
    payload = {"email": "test5@test.com", "password": "12345", "full_name": "Test"}
    response = client.post("/api/auth/register", json=payload)
    
    print(f"Status Code: {response.status_code}")
    assert response.status_code == 422
    print("✅ TEST PASSED")


def test_case_18_special_chars_in_password(client):
    """TC-AUTH-018: Password with special characters"""
    print("\n" + "="*60)
    print("TEST CASE 18: Password with Special Characters")
    print("="*60)
    
    payload = {"email": "special@test.com", "password": "P@ssw0rd!#$", "full_name": "Special Test"}
    response = client.post("/api/auth/register", json=payload)
    
    print(f"Status Code: {response.status_code}")
    assert response.status_code == 200
    assert "access_token" in response.json()
    print("✅ TEST PASSED")


def test_case_19_long_password(client):
    """TC-AUTH-019: Very long password (100 characters)"""
    print("\n" + "="*60)
    print("TEST CASE 19: Very Long Password")
    print("="*60)
    
    long_password = "A" * 100
    payload = {"email": "longpass@test.com", "password": long_password, "full_name": "Long Pass"}
    response = client.post("/api/auth/register", json=payload)
    
    print(f"Status Code: {response.status_code}")
    assert response.status_code == 200
    assert "access_token" in response.json()
    print("✅ TEST PASSED")


def test_case_20_email_with_plus(client):
    """TC-AUTH-020: Email with plus sign (valid email format)"""
    print("\n" + "="*60)
    print("TEST CASE 20: Email with Plus Sign")
    print("="*60)
    
    payload = {"email": "user+test@realestate.com", "password": "Password123", "full_name": "Plus Test"}
    response = client.post("/api/auth/register", json=payload)
    
    print(f"Status Code: {response.status_code}")
    assert response.status_code == 200
    assert "access_token" in response.json()
    print("✅ TEST PASSED")


def test_case_21_email_with_subdomain(client):
    """TC-AUTH-021: Email with subdomain"""
    print("\n" + "="*60)
    print("TEST CASE 21: Email with Subdomain")
    print("="*60)
    
    payload = {"email": "user@mail.realestate.com", "password": "Password123", "full_name": "Subdomain Test"}
    response = client.post("/api/auth/register", json=payload)
    
    print(f"Status Code: {response.status_code}")
    assert response.status_code == 200
    assert "access_token" in response.json()
    print("✅ TEST PASSED")


def test_case_22_full_name_with_spaces(client):
    """TC-AUTH-022: Full name with multiple spaces"""
    print("\n" + "="*60)
    print("TEST CASE 22: Full Name with Multiple Spaces")
    print("="*60)
    
    payload = {"email": "spaces@test.com", "password": "Password123", "full_name": "John   Doe   Smith"}
    response = client.post("/api/auth/register", json=payload)
    
    print(f"Status Code: {response.status_code}")
    assert response.status_code == 200
    print("✅ TEST PASSED")


def test_case_23_full_name_with_hyphen(client):
    """TC-AUTH-023: Full name with hyphen"""
    print("\n" + "="*60)
    print("TEST CASE 23: Full Name with Hyphen")
    print("="*60)
    
    payload = {"email": "hyphen@test.com", "password": "Password123", "full_name": "Mary-Jane Watson"}
    response = client.post("/api/auth/register", json=payload)
    
    print(f"Status Code: {response.status_code}")
    assert response.status_code == 200
    print("✅ TEST PASSED")


def test_case_24_login_after_registration(client):
    """TC-AUTH-024: Login immediately after registration"""
    print("\n" + "="*60)
    print("TEST CASE 24: Login After Registration")
    print("="*60)
    
    # Register
    reg_payload = {"email": "newlogin@test.com", "password": "Password123", "full_name": "New Login"}
    reg_response = client.post("/api/auth/register", json=reg_payload)
    assert reg_response.status_code == 200
    
    # Login with same credentials
    login_payload = {"email": "newlogin@test.com", "password": "Password123"}
    login_response = client.post("/api/auth/login", json=login_payload)
    
    print(f"Login Status Code: {login_response.status_code}")
    assert login_response.status_code == 200
    assert "access_token" in login_response.json()
    print("✅ TEST PASSED")


def test_case_25_multiple_registrations_different_emails(client):
    """TC-AUTH-025: Multiple registrations with different emails"""
    print("\n" + "="*60)
    print("TEST CASE 25: Multiple Registrations")
    print("="*60)
    
    emails = ["user1@test.com", "user2@test.com", "user3@test.com"]
    
    for email in emails:
        payload = {"email": email, "password": "Password123", "full_name": f"User {email}"}
        response = client.post("/api/auth/register", json=payload)
        assert response.status_code == 200
        print(f"✓ Registered: {email}")
    
    print("✅ TEST PASSED")
