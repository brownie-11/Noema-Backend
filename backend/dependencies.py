from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.models import User, Role
from backend.utils.token import decode_token

_scheme = HTTPBearer(auto_error=False)

_401 = HTTPException(status.HTTP_401_UNAUTHORIZED, "Not authenticated.",
                     headers={"WWW-Authenticate": "Bearer"})
_403 = HTTPException(status.HTTP_403_FORBIDDEN, "Admin access required.")


def get_current_user(
    creds: Optional[HTTPAuthorizationCredentials] = Depends(_scheme),
    db:    Session = Depends(get_db),
) -> User:
    if not creds:
        raise _401
    payload = decode_token(creds.credentials)
    if not payload:
        raise _401
    user_id = payload.get("sub")
    if not user_id:
        raise _401
    user = db.query(User).filter(User.id == int(user_id), User.is_active == True).first()  # noqa
    if not user:
        raise _401
    return user


def get_admin(user: User = Depends(get_current_user)) -> User:
    if user.role != Role.admin:
        raise _403
    return user


def get_optional_user(
    creds: Optional[HTTPAuthorizationCredentials] = Depends(_scheme),
    db:    Session = Depends(get_db),
) -> Optional[User]:
    if not creds:
        return None
    payload = decode_token(creds.credentials)
    if not payload:
        return None
    user_id = payload.get("sub")
    if not user_id:
        return None
    return db.query(User).filter(User.id == int(user_id), User.is_active == True).first()  # noqa
