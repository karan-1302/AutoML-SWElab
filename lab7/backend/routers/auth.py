# lab7/backend/routers/auth.py
# ─────────────────────────────────────────────────────────────
# Thin Router: Authentication
# Delegates all business logic to bll/auth_bll.py
# ─────────────────────────────────────────────────────────────

from fastapi import APIRouter, HTTPException, status
from models.schemas import LoginRequest, LoginResponse
from bll.auth_bll   import authenticate_user

router = APIRouter()


@router.post("/login", response_model=LoginResponse)
def login(body: LoginRequest):
    """
    Authenticate a real estate professional.
    The router is a thin layer — all business logic
    (validation, credential checking, JWT generation) is handled
    by the Business Logic Layer (auth_bll).
    """
    success, result = authenticate_user(body.email, body.password)

    if not success:
        raise HTTPException(
            status_code=result.get("code", 401),
            detail=result["errors"],
            headers={"WWW-Authenticate": "Bearer"} if result.get("code") == 401 else None,
        )

    return LoginResponse(
        access_token=result["access_token"],
        user=result["user"],
    )
