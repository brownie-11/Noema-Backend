import os
import threading
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import User, Role
from backend.schemas import SignupIn, LoginIn, TokenOut, UserOut, Msg
from backend.dependencies import get_current_user
from backend.utils.security import hash_password, verify_password
from backend.utils.token import create_token

router = APIRouter(tags=["Auth"])


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
    db.add(user); db.commit(); db.refresh(user)
    token = create_token(user.id, user.role.value)
    return TokenOut(access_token=token, user=UserOut.model_validate(user))


@router.post("/login", response_model=TokenOut)
def login(body: LoginIn, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == body.email).first()

    # Give a clear, specific error for each failure case
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


@router.post("/reset-password", response_model=Msg)
def reset_password(
    email:        str = Query(...),
    new_password: str = Query(..., min_length=8),
    reset_token:  str = Query(...),
    db: Session = Depends(get_db),
):
    secret = os.getenv("RESET_SECRET", "")
    if not secret:
        raise HTTPException(503, "Reset not configured. Set RESET_SECRET env var.")
    if reset_token != secret:
        raise HTTPException(403, "Invalid reset token.")
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(404, "No account with that email.")
    user.password_hash = hash_password(new_password)
    db.commit()
    return Msg(message=f"Password reset for @{user.username}. You can now log in.")
