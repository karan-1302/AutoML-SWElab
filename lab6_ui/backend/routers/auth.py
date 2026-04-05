# backend/routers/auth.py
# UC: Authentication
# POST /api/auth/login  → validates credentials → returns JWT

from fastapi import APIRouter, HTTPException, status
from models.schemas import LoginRequest, LoginResponse, UserOut
from utils.security import verify_password, create_access_token
from utils.store    import get_user

router = APIRouter()


@router.post("/login", response_model=LoginResponse)
def login(body: LoginRequest):
    """
    Authenticate a real estate professional.
    Returns a signed JWT that must be sent in the Authorization header
    for all subsequent requests.
    """
    user = get_user(body.email)

    # Check user exists and password matches
    if not user or not verify_password(body.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Build JWT payload
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
