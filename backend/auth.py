from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Session
from backend.models import User
from backend.utils.security import verify_password, hash_password
import logging

logger = logging.getLogger(__name__)


def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
    """
    Return the User if credentials are valid, else None.
    Handles corrupted hashes gracefully — never raises.
    """
    user = db.query(User).filter(User.email == email).first()
    if not user:
        return None
    if not user.is_active:
        return None

    # Guard: reject clearly corrupted or empty hashes before calling verify
    if not user.password_hash or not (
        user.password_hash.startswith("$2b$") or
        user.password_hash.startswith("$2a$")
    ):
        logger.warning(
            "Login blocked for @%s — password hash is corrupted. "
            "Use /reset-password to fix.", user.username
        )
        return None

    # Verify — bcrypt.checkpw never raises for valid hash format
    if not verify_password(password, user.password_hash):
        return None

    # Re-hash $2a$ (old format) to $2b$ silently
    if user.password_hash.startswith("$2a$"):
        user.password_hash = hash_password(password)
        logger.info("Upgraded hash format for @%s", user.username)

    user.last_login = datetime.utcnow()
    db.commit()
    return user
