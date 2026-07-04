import threading
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.models import User, Submission, SubmissionStatus, Role
from backend.schemas import SubmissionIn, SubmissionOut
from backend.dependencies import get_current_user

router = APIRouter(tags=["Submissions"])


@router.post("/submit-thought", response_model=SubmissionOut, status_code=201)
def submit(
    body: SubmissionIn,
    user: User = Depends(get_current_user),
    db:   Session = Depends(get_db),
):
    s = Submission(
        user_id=user.id, content=body.content,
        title=body.title, category=body.category or "other",
        status=SubmissionStatus.pending,
    )
    db.add(s); db.commit(); db.refresh(s)
    return s


@router.get("/submissions/public", response_model=list[SubmissionOut])
def public_submissions(
    skip: int = 0, limit: int = 100,
    category: str | None = None,
    db: Session = Depends(get_db),
):
    q = db.query(Submission).filter(Submission.status == SubmissionStatus.approved)
    if category and category != "all":
        q = q.filter(Submission.category == category)
    return q.order_by(Submission.created_at.desc()).offset(skip).limit(limit).all()


@router.get("/submissions/{sid}", response_model=SubmissionOut)
def get_submission(
    sid: int,
    user: User = Depends(get_current_user),
    db:   Session = Depends(get_db),
):
    s = db.query(Submission).filter(Submission.id == sid).first()
    if not s:
        raise HTTPException(404, "Submission not found.")
    if user.role != Role.admin and s.user_id != user.id:
        raise HTTPException(403, "Access denied.")
    return s
