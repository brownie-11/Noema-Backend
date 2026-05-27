import threading
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import User, Submission, SubmissionStatus, UserRole
from backend.schemas import SubmissionCreate, SubmissionPublic
from backend.dependencies import get_current_user
from backend.utils.email_service import send_submission_notification

router = APIRouter(tags=["Submissions"])


@router.post(
    "/submit-thought",
    response_model=SubmissionPublic,
    status_code=status.HTTP_201_CREATED,
)
def submit_thought(
    payload: SubmissionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Authenticated users submit a thought fragment.
    Saved as pending. Admin notified by email (async, non-blocking).
    """
    submission = Submission(
        user_id=current_user.id,
        content=payload.content,
        title=payload.title,
        category=payload.category or "other",
        status=SubmissionStatus.pending,
    )
    db.add(submission)
    db.commit()
    db.refresh(submission)

    def _notify():
        send_submission_notification(
            username=current_user.username,
            user_email=current_user.email,
            content=submission.content,
            submission_id=submission.id,
            title=submission.title,
            category=submission.category,
            timestamp=submission.created_at,
        )

    threading.Thread(target=_notify, daemon=True).start()
    return submission


@router.get("/submissions/public", response_model=list[SubmissionPublic])
def get_public_submissions(
    skip: int = 0,
    limit: int = 100,
    category: str | None = None,
    db: Session = Depends(get_db),
):
    """Return all approved submissions — visible to everyone in Explore Minds."""
    query = (
        db.query(Submission)
        .filter(Submission.status == SubmissionStatus.approved)
        .order_by(Submission.created_at.desc())
    )
    if category and category != "all":
        query = query.filter(Submission.category == category)
    return query.offset(skip).limit(limit).all()


@router.get("/submissions/{submission_id}", response_model=SubmissionPublic)
def get_submission(
    submission_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get a specific submission. Users see their own only; admins see all."""
    submission = db.query(Submission).filter(Submission.id == submission_id).first()
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found.")
    if current_user.role != UserRole.admin and submission.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied.")
    return submission
