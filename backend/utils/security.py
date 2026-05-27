import warnings
import logging

logger = logging.getLogger(__name__)

# Patch passlib to work with bcrypt 3.x without crashing
warnings.filterwarnings("ignore", ".*bcrypt.*")

try:
    from passlib.context import CryptContext
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    
    def hash_password(plain_password: str) -> str:
        return pwd_context.hash(plain_password)
    
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        if not hashed_password:
            return False
        if not hashed_password.startswith("$2b$") and not hashed_password.startswith("$2a$"):
            logger.warning("Invalid hash format detected")
            return False
        return pwd_context.verify(plain_password, hashed_password)

except Exception as e:
    logger.error("passlib failed to load: %s", e)
    import bcrypt as _bcrypt

    def hash_password(plain_password: str) -> str:
        return _bcrypt.hashpw(
            plain_password.encode(), _bcrypt.gensalt()
        ).decode()

    def verify_password(plain_password: str, hashed_password: str) -> bool:
        if not hashed_password:
            return False
        try:
            return _bcrypt.checkpw(
                plain_password.encode(),
                hashed_password.encode()
            )
        except Exception:
            return False
