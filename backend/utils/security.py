"""
Pure bcrypt password hashing.
No passlib. No wrappers. No version conflicts. Ever.
"""
import bcrypt


def hash_password(plain: str) -> str:
    """Hash a password. Always returns a $2b$ bcrypt string."""
    return bcrypt.hashpw(plain.encode("utf-8"), bcrypt.gensalt(rounds=12)).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    """Verify a password. Returns False for any bad input — never raises."""
    if not plain or not hashed:
        return False
    if not hashed.startswith(("$2b$", "$2a$")):
        return False
    try:
        return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
    except Exception:
        return False
