# backend/utils/security.py
# JWT creation / verification and password hashing helpers.
# Python 3.14 compatible: uses pure-Python hashlib instead of bcrypt.

import os
import hashlib
import secrets
from datetime import datetime, timedelta, timezone

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

# ── Config ────────────────────────────────────────────────────
SECRET_KEY  = os.getenv("JWT_SECRET_KEY", "cs331-super-secret-key-change-in-production")
ALGORITHM   = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 8  # 8 hours

# PBKDF2 configuration
PBKDF2_ITERATIONS = 100000
PBKDF2_HASH_NAME = "sha256"
SALT_LENGTH = 32

oauth2_scheme  = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

# ── Password helpers ──────────────────────────────────────────
def hash_password(plain: str) -> str:
    """
    Hash a password using PBKDF2-SHA256 with a random salt.
    Returns format: "salt:hash" (both hex-encoded).
    """
    salt = secrets.token_hex(SALT_LENGTH)
    hash_obj = hashlib.pbkdf2_hmac(
        PBKDF2_HASH_NAME,
        plain.encode('utf-8'),
        bytes.fromhex(salt),
        PBKDF2_ITERATIONS
    )
    return f"{salt}:{hash_obj.hex()}"

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain password against a stored hash.
    Expects hashed format: "salt:hash" (both hex-encoded).
    """
    try:
        # Split the stored string into salt and hash
        salt_hex, stored_hash = hashed_password.split(":")
        
        # Convert hex salt back to bytes
        salt_bytes = bytes.fromhex(salt_hex)
        
        # Recompute hash with same parameters
        new_hash = hashlib.pbkdf2_hmac(
            'sha256', 
            plain_password.encode('utf-8'), 
            salt_bytes,  # Use bytes, not string
            100000 
        )
        
        # Compare hex representations
        return new_hash.hex() == stored_hash
    except (ValueError, AttributeError):
        # Invalid hash format
        return False

# ── Token helpers ─────────────────────────────────────────────
def create_access_token(data: dict) -> str:
    """Create a JWT access token with expiration."""
    payload = data.copy()
    payload["exp"] = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def decode_token(token: str) -> dict:
    """Decode and validate a JWT token."""
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

# ── Dependency: get current user from JWT ─────────────────────
def get_current_user(token: str = Depends(oauth2_scheme)) -> dict:
    """Extract user info from JWT token."""
    payload = decode_token(token)
    user_id: str = payload.get("sub")
    if user_id is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")
    return {"user_id": user_id, "email": payload.get("email"), "name": payload.get("name")}

