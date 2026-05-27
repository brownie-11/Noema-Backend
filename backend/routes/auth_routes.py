import os
import threading
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import User, UserRole
from backend.schemas import (
    SignupRequest, LoginRequest, TokenResponse,
    UserPublic, MessageResponse, PasswordResetRequest,
)
from backend.auth import authenticate_user
from backend.dependencies import get_current_user
from backend.utils.security import hash_password
from backend.utils.token import create_access_token
from backend.utils.email_service import send_signup_notification

router = APIRouter(tags=["Authentication"])


@router.post("/signup", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def signup(payload: SignupRequest, db: Session = Depends(get_db)):
    """Create a new user account and return a JWT token."""
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
        is_active=True,
        last_login=datetime.utcnow(),
    )
    db.add(user)
    db.commit()
    db.refresh(user)

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
    """Return the currently authenticated user."""
    return current_user


@router.post("/reset-password", response_model=MessageResponse)
def reset_password(
    email: str = Query(...),
    new_password: str = Query(..., min_length=8),
    reset_token: str = Query(...),
    db: Session = Depends(get_db),
):
    """
    Emergency password reset via URL token.
    Set RESET_SECRET env var, then call:
      POST /reset-password?email=...&new_password=...&reset_token=<RESET_SECRET>
    """
    secret = os.getenv("RESET_SECRET", "")
    if not secret or reset_token != secret:
        raise HTTPException(status_code=403, detail="Invalid reset token.")
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    user.password_hash = hash_password(new_password)
    db.commit()
    return MessageResponse(message=f"Password reset for @{user.username}.")


@router.post("/logout", response_model=MessageResponse)
def logout(current_user: User = Depends(get_current_user)):
    """Stateless logout — client must discard the JWT."""
    return MessageResponse(
        message="You have left the mind space.",
        detail="Discard your token on the client side.",
    )
