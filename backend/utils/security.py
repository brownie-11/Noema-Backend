import warnings
from passlib.context import CryptContext

# Suppress passlib's bcrypt version warning
warnings.filterwarnings("ignore", ".*bcrypt.*", module="passlib")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(plain_password: str) -> str:
    return pwd_context.hash(plain_password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)
