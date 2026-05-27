from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Session
from backend.models import User
from backend.utils.security import verify_password, hash_password
import logging

logger = logging.getLogger(__name__)


def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
    user = db.query(User).filter(User.email == email).first()
    if not user:
        return None
    if not user.is_active:
        return None

    # Detect corrupted hash — doesn't start with valid bcrypt prefix
    hash_is_valid = (
        user.password_hash and
        (user.password_hash.startswith("$2b$") or
         user.password_hash.startswith("$2a$"))
    )

    if not hash_is_valid:
        # Hash is corrupted from the broken bcrypt install.
        # We can't verify the old password — log the issue.
        # The user will need to reset their password.
        logger.warning(
            "Corrupted hash for user @%s — cannot authenticate. "
            "Password reset required.", user.username
        )
        return None

    try:
        if not verify_password(password, user.password_hash):
            return None
    except Exception as e:
        logger.warning("Password verify error for @%s: %s", user.username, e)
        return None

    # Success — update last login and re-hash if using old $2a$ format
    if user.password_hash.startswith("$2a$"):
        user.password_hash = hash_password(password)
        logger.info("Re-hashed password for @%s to $2b$ format", user.username)

    user.last_login = datetime.utcnow()
    db.commit()
    return user
