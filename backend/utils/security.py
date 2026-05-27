"""
Password hashing using bcrypt directly.
Passlib removed entirely — it has a permanent version conflict with bcrypt 4.x
and bcrypt 3.x that causes UnknownHashError and AttributeError at runtime.
Using bcrypt directly is simpler, faster, and has zero dependency conflicts.
"""
import logging
import bcrypt

logger = logging.getLogger(__name__)


def hash_password(plain_password: str) -> str:
    """Hash a plain-text password. Always produces a $2b$ bcrypt hash."""
    pwd_bytes = plain_password.encode("utf-8")
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(pwd_bytes, salt)
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain-text password against a stored bcrypt hash.
    Returns False (never raises) for any invalid input.
    """
    if not plain_password or not hashed_password:
        return False

    # Reject anything that isn't a real bcrypt hash
    if not (hashed_password.startswith("$2b$") or hashed_password.startswith("$2a$")):
        logger.warning("verify_password: invalid hash format — not a bcrypt hash")
        return False

    try:
        return bcrypt.checkpw(
            plain_password.encode("utf-8"),
            hashed_password.encode("utf-8"),
        )
    except Exception as exc:
        logger.error("verify_password failed unexpectedly: %s", exc)
        return False
