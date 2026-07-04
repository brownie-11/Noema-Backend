"""
Noema Auth Routes
Includes proper forgot-password / reset-password flow:
1. POST /forgot-password  — user enters email, gets reset link via email
2. POST /reset-password   — user submits new password with token from email link
"""
import os
import secrets
import threading
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import Column, String, DateTime, Integer, ForeignKey
from pydantic import BaseModel, EmailStr

from backend.database import get_db, Base
from backend.models import User, Role
from backend.schemas import SignupIn, LoginIn, TokenOut, UserOut, Msg
from backend.dependencies import get_current_user
from backend.utils.security import hash_password, verify_password
from backend.utils.token import create_token
from backend.utils.email_service import (
    send_signup_notification,
    send_password_reset_email,
)

router = APIRouter(tags=["Auth"])


# ── Password Reset Token Model ────────────────────────────────────────────────

class PasswordResetToken(Base):
    """Stores one-time password reset tokens."""
    __tablename__ = "password_reset_tokens"

    id         = Column(Integer, primary_key=True)
    user_id    = Column(Integer, ForeignKey("users.id"), nullable=False)
    token      = Column(String(128), unique=True, nullable=False, index=True)
    expires_at = Column(DateTime, nullable=False)
    used       = Column(Integer, default=0)  # 0=unused, 1=used


# ── Request/Response schemas ──────────────────────────────────────────────────

class ForgotPasswordIn(BaseModel):
    email: EmailStr


class ResetPasswordIn(BaseModel):
    token: str
    new_password: str


# ── Routes ────────────────────────────────────────────────────────────────────

@router.post("/signup", response_model=TokenOut, status_code=201)
def signup(body: SignupIn, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == body.email).first():
        raise HTTPException(409, "Email already registered.")
    if db.query(User).filter(User.username == body.username).first():
        raise HTTPException(409, "Username already taken.")

    user = User(
        username=body.username,
        email=body.email,
        password_hash=hash_password(body.password),
        role=Role.user,
        last_login=datetime.utcnow(),
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    # Notify admin — async, never blocks
    threading.Thread(
        target=send_signup_notification,
        args=(user.username, user.email, user.created_at),
        daemon=True,
    ).start()

    token = create_token(user.id, user.role.value)
    return TokenOut(access_token=token, user=UserOut.model_validate(user))


@router.post("/login", response_model=TokenOut)
def login(body: LoginIn, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == body.email).first()

    if not user:
        raise HTTPException(401, "No account found with that email.")
    if not user.is_active:
        raise HTTPException(401, "This account has been deactivated.")
    if not verify_password(body.password, user.password_hash):
        raise HTTPException(401, "Incorrect password.")

    user.last_login = datetime.utcnow()
    db.commit()

    token = create_token(user.id, user.role.value)
    return TokenOut(access_token=token, user=UserOut.model_validate(user))


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)):
    return user


@router.post("/logout", response_model=Msg)
def logout(user: User = Depends(get_current_user)):
    return Msg(message="You have left the mind space.")


@router.post("/forgot-password", response_model=Msg)
def forgot_password(body: ForgotPasswordIn, db: Session = Depends(get_db)):
    """
    Step 1 of password reset.
    User enters their email. If account exists, we send a reset link.
    Always returns success message — never reveals if email exists.
    """
    user = db.query(User).filter(User.email == body.email).first()

    # Always return same message — don't leak whether email exists
    success_msg = Msg(
        message="If an account exists with that email, a reset link has been sent."
    )

    if not user or not user.is_active:
        return success_msg  # silent — don't reveal account existence

    # Delete any existing unused tokens for this user
    db.query(PasswordResetToken).filter(
        PasswordResetToken.user_id == user.id,
        PasswordResetToken.used == 0,
    ).delete()

    # Create new token — expires in 1 hour
    raw_token = secrets.token_urlsafe(48)
    reset_token = PasswordResetToken(
        user_id=user.id,
        token=raw_token,
        expires_at=datetime.utcnow() + timedelta(hours=1),
        used=0,
    )
    db.add(reset_token)
    db.commit()

    # Get frontend URL from env — where the reset form lives
    frontend_url = os.getenv(
        "FRONTEND_URL",
        "https://noema-minds.netlify.app"
    )

    # Send email async — never blocks
    def _send():
        send_password_reset_email(
            user_email=user.email,
            username=user.username,
            reset_token=raw_token,
            frontend_url=frontend_url,
        )
    threading.Thread(target=_send, daemon=True).start()

    return success_msg


@router.post("/reset-password", response_model=Msg)
def reset_password(body: ResetPasswordIn, db: Session = Depends(get_db)):
    """
    Step 2 of password reset.
    User submits the token from the email link + their new password.
    """
    if len(body.new_password) < 8:
        raise HTTPException(400, "Password must be at least 8 characters.")

    # Find the token
    record = db.query(PasswordResetToken).filter(
        PasswordResetToken.token == body.token,
        PasswordResetToken.used == 0,
    ).first()

    if not record:
        raise HTTPException(400, "Invalid or expired reset link. Please request a new one.")

    if datetime.utcnow() > record.expires_at:
        db.delete(record)
        db.commit()
        raise HTTPException(400, "This reset link has expired. Please request a new one.")

    # Find the user and update password
    user = db.query(User).filter(User.id == record.user_id).first()
    if not user:
        raise HTTPException(404, "Account not found.")

    user.password_hash = hash_password(body.new_password)
    record.used = 1  # mark token as used
    db.commit()

    return Msg(message=f"Password updated for @{user.username}. You can now log in.")
