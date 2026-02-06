# backend/routers/auth.py
# Layer 2: Authentication router
# POST /api/auth/login  →  BLL verifies credentials  →  returns JWT
# Maps to UC-01: Login  (Lab 4 Section V)

from fastapi import APIRouter, HTTPException, status
from models.schemas import LoginRequest, LoginResponse, UserOut
from utils.security import verify_password, create_access_token
from utils.store    import get_user

router = APIRouter()


@router.post("/login", response_model=LoginResponse)
def login(body: LoginRequest):
    """
    Authenticate a real estate professional.

    Layer flow (Lab 4 Section II — "When a user logs in"):
      Layer 2 → BLL AuthManager.verifyCredentials() → DAL queries D1 → JWT returned
    """
    user = get_user(body.email)

    if not user or not verify_password(body.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = create_access_token({
        "sub":   user["user_id"],
        "email": user["email"],
        "name":  user["name"],
    })

    return LoginResponse(
        access_token=token,
        user=UserOut(
            user_id=user["user_id"],
            email=user["email"],
            name=user["name"],
        ),
    )
