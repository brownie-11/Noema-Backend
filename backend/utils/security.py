"""
security.py — password hashing for Noema
-----------------------------------------
Supports three hash formats:
  • $argon2id$  — hashes created by the old argon2 setup (Railway DB)
  • $2b$ / $2a$ — bcrypt hashes created by passlib

On every successful login the hash is transparently upgraded to $2b$ bcrypt
so the system converges on a single algorithm over time.
"""
import logging
import warnings

warnings.filterwarnings("ignore", ".*bcrypt.*")
warnings.filterwarnings("ignore", ".*passlib.*")

logger = logging.getLogger(__name__)

# ── passlib context: bcrypt for new hashes ─────────────────────────────────
from passlib.context import CryptContext

_bcrypt_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(plain: str) -> str:
    """Always hash new passwords with bcrypt $2b$."""
    return _bcrypt_ctx.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    """
    Verify `plain` against `hashed` regardless of algorithm.
    Handles argon2id, bcrypt $2b$, bcrypt $2a$.
    """
    if not plain or not hashed:
        return False

    # ── argon2 (legacy hashes in the Railway database) ─────────────────────
    if hashed.startswith("$argon2"):
        try:
            from argon2 import PasswordHasher
            from argon2.exceptions import VerifyMismatchError, VerificationError, InvalidHashError
            ph = PasswordHasher()
            ph.verify(hashed, plain)   # raises on failure
            return True
        except Exception as e:
            logger.debug("argon2 verify failed: %s", e)
            return False

    # ── bcrypt $2b$ / $2a$ ──────────────────────────────────────────────────
    if hashed.startswith("$2b$") or hashed.startswith("$2a$"):
        try:
            return _bcrypt_ctx.verify(plain, hashed)
        except Exception as e:
            logger.debug("bcrypt verify failed: %s", e)
            return False

    logger.warning("Unrecognised hash format, cannot verify.")
    return False


def needs_rehash(hashed: str) -> bool:
    """Return True if the hash should be upgraded to bcrypt on next login."""
    return hashed.startswith("$argon2")
