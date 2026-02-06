# lab8/backend/bll/auth_bll.py
# ─────────────────────────────────────────────────────────────
# Authentication Business Logic Layer
#
# Updated for Lab 8: now uses the DAL (user_repository) instead
# of the in-memory store for user lookups.
#
# Business Rules Implemented:
#   BR-AUTH-01  Email must be a valid email format.
#   BR-AUTH-02  Both email and password fields are required.
#   BR-AUTH-03  Password must be at least 6 characters.
#   BR-AUTH-04  User must exist in the database.
#   BR-AUTH-05  Password hash must match stored hash.
#   BR-AUTH-06  JWT token is generated with user claims (sub, email, name).
#   BR-AUTH-07  Token expires after 8 hours.
# ─────────────────────────────────────────────────────────────

import re
from typing import Tuple

from sqlalchemy.orm import Session

from models.schemas import LoginResponse, UserOut
from utils.security import verify_password, create_access_token
from dal.repositories.user_repository import get_user_by_email


# ── Validation helpers ────────────────────────────────────────

EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")
MIN_PASSWORD_LENGTH = 6


def _validate_credentials(email: str, password: str) -> list[str]:
    """
    Validate login input fields.
    Returns a list of error messages (empty = valid).
    """
    errors: list[str] = []

    # BR-AUTH-02: Both fields required
    if not email or not email.strip():
        errors.append("Email address is required.")
    if not password:
        errors.append("Password is required.")

    if errors:
        return errors  # Short-circuit — no point checking format

    # BR-AUTH-01: Valid email format
    if not EMAIL_REGEX.match(email.strip()):
        errors.append("Email address is not in a valid format (e.g. user@domain.com).")

    # BR-AUTH-03: Minimum password length
    if len(password) < MIN_PASSWORD_LENGTH:
        errors.append(f"Password must be at least {MIN_PASSWORD_LENGTH} characters.")

    return errors


# ── Core BLL function ─────────────────────────────────────────

def authenticate_user(email: str, password: str, db: Session) -> Tuple[bool, dict]:
    """
    Authenticate a user by validating inputs, checking credentials
    against the database (DAL), and generating a JWT token.

    Parameters
    ----------
    email : str
        User's email address.
    password : str
        User's password.
    db : Session
        SQLAlchemy database session (injected via DAL).

    Returns
    -------
    (success, payload)
        On success: (True, {"access_token": ..., "user": UserOut(...)})
        On failure: (False, {"errors": [str, ...], "code": int})
    """
    # ── Step 1: Input validation ─────────────────────────────
    validation_errors = _validate_credentials(email, password)
    if validation_errors:
        return False, {"errors": validation_errors, "code": 422}

    email = email.strip().lower()

    # ── Step 2: Check user exists via DAL (BR-AUTH-04) ────────
    user = get_user_by_email(db, email)
    if not user:
        return False, {
            "errors": ["Incorrect email or password."],
            "code": 401,
        }

    # ── Step 3: Verify password hash (BR-AUTH-05) ────────────
    if not verify_password(password, user.hashed_password):
        return False, {
            "errors": ["Incorrect email or password."],
            "code": 401,
        }

    # ── Step 4: Generate JWT (BR-AUTH-06 / BR-AUTH-07) ───────
    token = create_access_token({
        "sub":   user.user_id,
        "email": user.email,
        "name":  user.full_name,
    })

    return True, {
        "access_token": token,
        "user": UserOut(
            user_id=user.user_id,
            email=user.email,
            full_name=user.full_name,
        ),
    }



# ── Registration BLL function ─────────────────────────────────

def register_user(email: str, password: str, full_name: str, db: Session) -> Tuple[bool, dict]:
    """
    Register a new user account.
    Validates input, checks for duplicates, hashes password with PBKDF2,
    and stores in Supabase via DAL.

    Parameters
    ----------
    email : str
        User's email address.
    password : str
        User's password (plain text).
    full_name : str
        User's full name.
    db : Session
        SQLAlchemy database session (injected via DAL).

    Returns
    -------
    (success, payload)
        On success: (True, {"access_token": ..., "user": UserOut(...)})
        On failure: (False, {"errors": [str, ...], "code": int})
    """
    # ── Step 1: Input validation ─────────────────────────────
    errors: list[str] = []

    # Validate email
    if not email or not email.strip():
        errors.append("Email address is required.")
    elif not EMAIL_REGEX.match(email.strip()):
        errors.append("Email address is not in a valid format (e.g. user@domain.com).")

    # Validate password
    if not password:
        errors.append("Password is required.")
    elif len(password) < MIN_PASSWORD_LENGTH:
        errors.append(f"Password must be at least {MIN_PASSWORD_LENGTH} characters.")

    # Validate full_name
    if not full_name or not full_name.strip():
        errors.append("Full name is required.")

    if errors:
        return False, {"errors": errors, "code": 422}

    email = email.strip().lower()
    full_name = full_name.strip()

    # ── Step 2: Check if user already exists ─────────────────
    existing_user = get_user_by_email(db, email)
    if existing_user:
        return False, {
            "errors": ["An account with this email address already exists."],
            "code": 409,
        }

    # ── Step 3: Hash password with PBKDF2 ────────────────────
    from utils.security import hash_password
    hashed_password = hash_password(password)

    # ── Step 4: Create user via DAL ──────────────────────────
    from dal.repositories.user_repository import create_user
    import uuid

    try:
        # Generate a unique user_id
        user_id = f"user-{uuid.uuid4().hex[:12]}"

        new_user = create_user(
            db=db,
            user_id=user_id,
            email=email,
            full_name=full_name,
            hashed_password=hashed_password,
        )

        # ── Step 5: Generate JWT token ───────────────────────
        token = create_access_token({
            "sub":   new_user.user_id,
            "email": new_user.email,
            "name":  new_user.full_name,
        })

        return True, {
            "access_token": token,
            "user": UserOut(
                user_id=new_user.user_id,
                email=new_user.email,
                full_name=new_user.full_name,
            ),
        }

    except Exception as e:
        # Database error (e.g., constraint violation)
        return False, {
            "errors": ["Failed to create user account. Please try again."],
            "code": 500,
        }
