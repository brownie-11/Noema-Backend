"""
auth.py — user authentication logic
"""
from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Session
from backend.models import User
from backend.utils.security import verify_password, hash_password, needs_rehash
import logging

logger = logging.getLogger(__name__)


def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
    """
    Verify credentials. Returns the User on success, None on failure.

    Hash upgrade path:
      - If stored hash is argon2id (old Railway DB), verify with argon2,
        then re-hash to bcrypt so future logins use bcrypt.
      - If stored hash is already bcrypt ($2b$), verify normally.
    """
    user = db.query(User).filter(User.email == email).first()
    if not user:
        logger.debug("Login attempt: email not found → %s", email)
        return None

    if not user.is_active:
        logger.info("Login attempt for inactive account @%s", user.username)
        return None

    if not user.password_hash:
        logger.warning("User @%s has no password hash — account corrupt", user.username)
        return None

    # Verify password (handles argon2 and bcrypt transparently)
    if not verify_password(password, user.password_hash):
        logger.debug("Bad password for @%s", user.username)
        return None

    # Transparently upgrade hash algorithm: argon2 → bcrypt
    if needs_rehash(user.password_hash):
        try:
            user.password_hash = hash_password(password)
            logger.info("Upgraded hash to bcrypt for @%s", user.username)
        except Exception as e:
            logger.warning("Hash upgrade failed for @%s: %s", user.username, e)

    user.last_login = datetime.utcnow()
    db.commit()
    return user
