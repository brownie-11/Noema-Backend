from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.models import User, Submission
from backend.schemas import UserOut, SubmissionOut
from backend.dependencies import get_current_user

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/me/submissions", response_model=list[SubmissionOut])
def my_submissions(
    skip: int = 0, limit: int = 50,
    user: User = Depends(get_current_user),
    db:   Session = Depends(get_db),
):
    return (
        db.query(Submission)
        .filter(Submission.user_id == user.id)
        .order_by(Submission.created_at.desc())
        .offset(skip).limit(limit).all()
    )


@router.get("/{user_id}", response_model=UserOut)
def get_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id, User.is_active == True).first()  # noqa
    if not user:
        raise HTTPException(404, "User not found.")
    return user
