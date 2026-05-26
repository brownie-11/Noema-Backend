from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import (
    User, Submission, ThoughtNode, ThoughtConnection,
    SubmissionStatus, UserRole
)
from backend.schemas import (
    UserAdmin, SubmissionWithUser, ThoughtNodeCreate, ThoughtNodePublic,
    ConnectionCreate, ConnectionPublic, SubmissionReview, MessageResponse
)
from backend.dependencies import get_current_admin

router = APIRouter(prefix="/admin", tags=["Admin"])


# ── Users ─────────────────────────────────────────────────────────────────────

@router.get("/users", response_model=list[UserAdmin])
def list_users(
    skip: int = 0,
    limit: int = 100,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """List all registered users with submission counts."""
    users = db.query(User).order_by(User.created_at.desc()).offset(skip).limit(limit).all()
    result = []
    for u in users:
        count = db.query(Submission).filter(Submission.user_id == u.id).count()
        ua = UserAdmin.model_validate(u)
        ua.submission_count = count
        result.append(ua)
    return result


@router.delete("/users/{user_id}", response_model=MessageResponse)
def deactivate_user(
    user_id: int,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Soft-delete (deactivate) a user account."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    if user.role == UserRole.admin:
        raise HTTPException(status_code=403, detail="Cannot deactivate another admin.")
    user.is_active = False
    db.commit()
    return MessageResponse(message=f"User @{user.username} deactivated.")


# ── Submissions ───────────────────────────────────────────────────────────────

@router.get("/submissions", response_model=list[SubmissionWithUser])
def list_submissions(
    status_filter: str | None = None,
    skip: int = 0,
    limit: int = 100,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """List all submissions, optionally filtered by status."""
    query = db.query(Submission).order_by(Submission.created_at.desc())
    if status_filter:
        try:
            s = SubmissionStatus(status_filter)
            query = query.filter(Submission.status == s)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid status: {status_filter}")
    return query.offset(skip).limit(limit).all()


@router.post("/approve/{submission_id}", response_model=MessageResponse)
def approve_submission(
    submission_id: int,
    payload: SubmissionReview | None = None,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Approve a submission — it will appear in the public Explore Minds feed."""
    sub = db.query(Submission).filter(Submission.id == submission_id).first()
    if not sub:
        raise HTTPException(status_code=404, detail="Submission not found.")
    sub.status = SubmissionStatus.approved
    sub.reviewed_at = datetime.utcnow()
    if payload and payload.note:
        sub.admin_note = payload.note
    db.commit()
    return MessageResponse(message=f"Submission #{submission_id} approved.")


@router.post("/reject/{submission_id}", response_model=MessageResponse)
def reject_submission(
    submission_id: int,
    payload: SubmissionReview | None = None,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Reject a submission."""
    sub = db.query(Submission).filter(Submission.id == submission_id).first()
    if not sub:
        raise HTTPException(status_code=404, detail="Submission not found.")
    sub.status = SubmissionStatus.rejected
    sub.reviewed_at = datetime.utcnow()
    if payload and payload.note:
        sub.admin_note = payload.note
    db.commit()
    return MessageResponse(message=f"Submission #{submission_id} rejected.")


@router.delete("/submissions/{submission_id}", response_model=MessageResponse)
def delete_submission(
    submission_id: int,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Permanently delete a submission (spam removal)."""
    sub = db.query(Submission).filter(Submission.id == submission_id).first()
    if not sub:
        raise HTTPException(status_code=404, detail="Submission not found.")
    db.delete(sub)
    db.commit()
    return MessageResponse(message=f"Submission #{submission_id} deleted.")


# ── Thought Architecture ──────────────────────────────────────────────────────

@router.post("/create-node", response_model=ThoughtNodePublic, status_code=201)
def create_node(
    payload: ThoughtNodeCreate,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Create a new curated thought node in the constellation."""
    CAT_COLORS = {
        "consciousness": "#c8a97e", "existence": "#c8a07e", "time": "#8bb5c8",
        "memory": "#8bb5c8", "love": "#a07ec8", "fear": "#c87e8a",
        "dreams": "#7ec8a0", "philosophy": "#b0c87e", "human": "#c8b07e",
        "other": "#7a7672",
    }
    node = ThoughtNode(
        title=payload.title,
        content=payload.content,
        category=payload.category,
        author=payload.author,
        position_x=payload.position_x,
        position_y=payload.position_y,
        node_radius=payload.node_radius,
        hex_color=payload.hex_color or CAT_COLORS.get(payload.category, "#7a7672"),
        is_base=False,
        created_by=admin.id,
    )
    db.add(node)
    db.commit()
    db.refresh(node)
    return node


@router.patch("/nodes/{node_id}", response_model=ThoughtNodePublic)
def edit_node(
    node_id: int,
    payload: ThoughtNodePublic,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Edit any field of a thought node."""
    node = db.query(ThoughtNode).filter(ThoughtNode.id == node_id).first()
    if not node:
        raise HTTPException(status_code=404, detail="Node not found.")
    for field, val in payload.model_dump(exclude_unset=True).items():
        if hasattr(node, field) and field not in ("id", "created_at", "is_base"):
            setattr(node, field, val)
    db.commit()
    db.refresh(node)
    return node


@router.delete("/nodes/{node_id}", response_model=MessageResponse)
def delete_node(
    node_id: int,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Delete a thought node (and its connections). Base nodes are protected."""
    node = db.query(ThoughtNode).filter(ThoughtNode.id == node_id).first()
    if not node:
        raise HTTPException(status_code=404, detail="Node not found.")
    if node.is_base:
        raise HTTPException(status_code=403, detail="Curator base nodes cannot be deleted.")
    db.delete(node)
    db.commit()
    return MessageResponse(message=f"Node '{node.title}' removed from the constellation.")


@router.post("/connect-nodes", response_model=ConnectionPublic, status_code=201)
def connect_nodes(
    payload: ConnectionCreate,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Create a connection between two thought nodes."""
    # Verify both nodes exist
    src = db.query(ThoughtNode).filter(ThoughtNode.id == payload.source_node_id).first()
    tgt = db.query(ThoughtNode).filter(ThoughtNode.id == payload.target_node_id).first()
    if not src:
        raise HTTPException(status_code=404, detail=f"Source node #{payload.source_node_id} not found.")
    if not tgt:
        raise HTTPException(status_code=404, detail=f"Target node #{payload.target_node_id} not found.")

    # Prevent duplicate connections of the same type
    existing = db.query(ThoughtConnection).filter(
        ThoughtConnection.source_node_id == payload.source_node_id,
        ThoughtConnection.target_node_id == payload.target_node_id,
        ThoughtConnection.connection_type == payload.connection_type,
    ).first()
    if existing:
        raise HTTPException(status_code=409, detail="This connection already exists.")

    conn = ThoughtConnection(
        source_node_id=payload.source_node_id,
        target_node_id=payload.target_node_id,
        connection_type=payload.connection_type,
    )
    db.add(conn)
    db.commit()
    db.refresh(conn)
    return conn


@router.delete("/connections/{conn_id}", response_model=MessageResponse)
def delete_connection(
    conn_id: int,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Remove a connection between nodes."""
    conn = db.query(ThoughtConnection).filter(ThoughtConnection.id == conn_id).first()
    if not conn:
        raise HTTPException(status_code=404, detail="Connection not found.")
    db.delete(conn)
    db.commit()
    return MessageResponse(message=f"Connection #{conn_id} removed.")


# ── Promote submission → node ─────────────────────────────────────────────────

@router.post("/promote/{submission_id}", response_model=ThoughtNodePublic, status_code=201)
def promote_submission_to_node(
    submission_id: int,
    node_data: ThoughtNodeCreate | None = None,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """
    One-click: approve a submission AND create a thought node from it.
    Optionally override position/category via node_data.
    """
    sub = db.query(Submission).filter(Submission.id == submission_id).first()
    if not sub:
        raise HTTPException(status_code=404, detail="Submission not found.")

    sub.status = SubmissionStatus.approved
    sub.reviewed_at = datetime.utcnow()

    import random
    node = ThoughtNode(
        title=node_data.title if node_data and node_data.title else (sub.title or sub.content[:60]),
        content=node_data.content if node_data and node_data.content else sub.content,
        category=node_data.category if node_data else (sub.category or "other"),
        author=sub.user.username if sub.user else "anonymous",
        position_x=node_data.position_x if node_data else round(random.uniform(0.1, 0.9), 3),
        position_y=node_data.position_y if node_data else round(random.uniform(0.1, 0.9), 3),
        node_radius=14.0,
        is_base=False,
        created_by=admin.id,
    )
    db.add(node)
    db.flush()
    sub.thought_node_id = node.id
    db.commit()
    db.refresh(node)
    return node
