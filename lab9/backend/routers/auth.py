# lab8/backend/routers/auth.py
# ─────────────────────────────────────────────────────────────
# Thin Router: Authentication
# Delegates all business logic to bll/auth_bll.py
# Updated for Lab 8: injects database session via DAL.
# ─────────────────────────────────────────────────────────────

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from models.schemas import LoginRequest, LoginResponse
from bll.auth_bll   import authenticate_user
from dal.database   import get_db

router = APIRouter()


@router.post("/login", response_model=LoginResponse)
def login(body: LoginRequest, db: Session = Depends(get_db)):
    """
    Authenticate a real estate professional.
    The router is a thin layer — all business logic is handled
    by the Business Logic Layer (auth_bll) with DAL integration.
    """
    success, result = authenticate_user(body.email, body.password, db)

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
