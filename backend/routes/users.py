from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import User
from backend.schemas import UserPublic, SubmissionPublic
from backend.dependencies import get_current_user

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/me/submissions", response_model=list[SubmissionPublic])
def my_submissions(
    skip: int = 0,
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Return all submissions belonging to the current user."""
    from backend.models import Submission
    submissions = (
        db.query(Submission)
        .filter(Submission.user_id == current_user.id)
        .order_by(Submission.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    return submissions


@router.get("/{user_id}", response_model=UserPublic)
def get_user_profile(user_id: int, db: Session = Depends(get_db)):
    """Return a public user profile by ID."""
    user = db.query(User).filter(User.id == user_id, User.is_active == True).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
    return user
