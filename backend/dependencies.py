from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.models import User, UserRole
from backend.utils.token import decode_access_token

bearer_scheme = HTTPBearer(auto_error=False)

_401 = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Not authenticated. Please log in.",
    headers={"WWW-Authenticate": "Bearer"},
)
_403 = HTTPException(
    status_code=status.HTTP_403_FORBIDDEN,
    detail="Admin access required.",
)


def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    """Resolve a Bearer JWT to the authenticated User. Raises 401 if invalid."""
    if credentials is None:
        raise _401

    payload = decode_access_token(credentials.credentials)
    if payload is None:
        raise _401

    user_id = payload.get("sub")
    if user_id is None:
        raise _401

    user = db.query(User).filter(User.id == int(user_id)).first()
    if user is None or not user.is_active:
        raise _401

    return user


def get_current_admin(current_user: User = Depends(get_current_user)) -> User:
    """Require admin role. Raises 403 for regular users."""
    if current_user.role != UserRole.admin:
        raise _403
    return current_user


def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> Optional[User]:
    """Like get_current_user but returns None for unauthenticated requests."""
    if credentials is None:
        return None
    payload = decode_access_token(credentials.credentials)
    if payload is None:
        return None
    user_id = payload.get("sub")
    if user_id is None:
        return None
    return db.query(User).filter(
        User.id == int(user_id),
        User.is_active == True  # noqa: E712
    ).first()
