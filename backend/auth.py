from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Session
from backend.models import User
from backend.utils.security import verify_password


def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
    """
    Return the User if credentials are valid, else None.
    Also updates last_login timestamp on success.
    """
    user = db.query(User).filter(User.email == email).first()
    if not user:
        return None
    if not verify_password(password, user.password_hash):
        return None
    if not user.is_active:
        return None
    user.last_login = datetime.utcnow()
    db.commit()
    return user
