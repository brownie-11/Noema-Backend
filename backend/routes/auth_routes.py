import os
import threading
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import User, UserRole
from backend.schemas import (
    SignupRequest, LoginRequest, TokenResponse, UserPublic, MessageResponse
)
from backend.auth import authenticate_user
from backend.dependencies import get_current_user
from backend.utils.security import hash_password
from backend.utils.token import create_access_token
from backend.utils.email_service import send_signup_notification

router = APIRouter(tags=["Authentication"])


@router.post("/signup", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def signup(payload: SignupRequest, db: Session = Depends(get_db)):
    """Create a new account and return a JWT token."""

    if db.query(User).filter(User.email == payload.email).first():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists.",
        )
    if db.query(User).filter(User.username == payload.username).first():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This username is already taken.",
        )

    user = User(
        username=payload.username,
        email=payload.email,
        password_hash=hash_password(payload.password),
        role=UserRole.user,
        last_login=datetime.utcnow(),
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    # Admin notification — async, never blocks the response
    threading.Thread(
        target=send_signup_notification,
        args=(user.username, user.email, user.created_at),
        daemon=True,
    ).start()

    token = create_access_token(data={"sub": str(user.id), "role": user.role.value})
    return TokenResponse(access_token=token, user=UserPublic.model_validate(user))


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    """Authenticate and return a JWT token."""
    user = authenticate_user(db, email=payload.email, password=payload.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = create_access_token(data={"sub": str(user.id), "role": user.role.value})
    return TokenResponse(access_token=token, user=UserPublic.model_validate(user))


@router.get("/me", response_model=UserPublic)
def get_me(current_user: User = Depends(get_current_user)):
    """Return the authenticated user's profile."""
    return current_user


@router.post("/reset-password", response_model=MessageResponse)
def reset_password(
    email:         str = Query(..., description="Account email to reset"),
    new_password:  str = Query(..., min_length=8, description="New password"),
    reset_token:   str = Query(..., description="Must match RESET_SECRET env var"),
    db: Session = Depends(get_db),
):
    """
    Emergency password reset.
    Requires the RESET_SECRET env var to be set on Railway.
    Call from /docs: POST /reset-password?email=x&new_password=y&reset_token=z
    """
    secret = os.getenv("RESET_SECRET", "").strip()
    if not secret:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Password reset is not configured. Set RESET_SECRET env var.",
        )
    if reset_token != secret:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid reset token.",
        )

    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="No account found with that email.")

    user.password_hash = hash_password(new_password)
    db.commit()
    return MessageResponse(message=f"Password reset for @{user.username}. You can now log in.")


@router.post("/logout", response_model=MessageResponse)
def logout(current_user: User = Depends(get_current_user)):
    """Stateless logout — client must discard the token."""
    return MessageResponse(
        message="You have left the mind space.",
        detail="Discard your token on the client side.",
    )
