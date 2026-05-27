import random
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import (
    User, Submission, ThoughtNode, ThoughtConnection,
    SubmissionStatus, UserRole,
)
from backend.schemas import (
    UserAdmin, SubmissionWithUser, ThoughtNodeCreate, ThoughtNodeUpdate,
    ThoughtNodePublic, ConnectionCreate, ConnectionPublic,
    SubmissionReview, MessageResponse,
)
from backend.dependencies import get_current_admin

router = APIRouter(prefix="/admin", tags=["Admin"])

CAT_COLORS = {
    "consciousness": "#c8a97e", "existence": "#c8a07e", "time": "#8bb5c8",
    "memory": "#8bb5c8", "love": "#a07ec8", "fear": "#c87e8a",
    "dreams": "#7ec8a0", "philosophy": "#b0c87e", "human": "#c8b07e",
    "fragment": "#8bb5c8", "other": "#7a7672",
}


# ── Users ─────────────────────────────────────────────────────────────────────

@router.get("/users", response_model=list[UserAdmin])
def list_users(
    skip: int = 0,
    limit: int = 100,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
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
    query = db.query(Submission).order_by(Submission.created_at.desc())
    if status_filter:
        try:
            query = query.filter(Submission.status == SubmissionStatus(status_filter))
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
    sub = db.query(Submission).filter(Submission.id == submission_id).first()
    if not sub:
        raise HTTPException(status_code=404, detail="Submission not found.")
    sub.status      = SubmissionStatus.approved
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
    sub = db.query(Submission).filter(Submission.id == submission_id).first()
    if not sub:
        raise HTTPException(status_code=404, detail="Submission not found.")
    sub.status      = SubmissionStatus.rejected
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
    sub = db.query(Submission).filter(Submission.id == submission_id).first()
    if not sub:
        raise HTTPException(status_code=404, detail="Submission not found.")
    db.delete(sub)
    db.commit()
    return MessageResponse(message=f"Submission #{submission_id} deleted.")


# ── Constellation ─────────────────────────────────────────────────────────────

@router.post("/create-node", response_model=ThoughtNodePublic, status_code=201)
def create_node(
    payload: ThoughtNodeCreate,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
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
    payload: ThoughtNodeUpdate,   # FIX: was ThoughtNodePublic — wrong schema for a PATCH
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    node = db.query(ThoughtNode).filter(ThoughtNode.id == node_id).first()
    if not node:
        raise HTTPException(status_code=404, detail="Node not found.")
    update_data = payload.model_dump(exclude_unset=True)
    for field, val in update_data.items():
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
    node = db.query(ThoughtNode).filter(ThoughtNode.id == node_id).first()
    if not node:
        raise HTTPException(status_code=404, detail="Node not found.")
    if node.is_base:
        raise HTTPException(status_code=403, detail="Curator base nodes cannot be deleted.")
    db.delete(node)
    db.commit()
    return MessageResponse(message=f"Node '{node.title}' removed.")


@router.post("/connect-nodes", response_model=ConnectionPublic, status_code=201)
def connect_nodes(
    payload: ConnectionCreate,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    src = db.query(ThoughtNode).filter(ThoughtNode.id == payload.source_node_id).first()
    tgt = db.query(ThoughtNode).filter(ThoughtNode.id == payload.target_node_id).first()
    if not src:
        raise HTTPException(status_code=404, detail=f"Source node #{payload.source_node_id} not found.")
    if not tgt:
        raise HTTPException(status_code=404, detail=f"Target node #{payload.target_node_id} not found.")

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
    conn = db.query(ThoughtConnection).filter(ThoughtConnection.id == conn_id).first()
    if not conn:
        raise HTTPException(status_code=404, detail="Connection not found.")
    db.delete(conn)
    db.commit()
    return MessageResponse(message=f"Connection #{conn_id} removed.")


@router.post("/promote/{submission_id}", response_model=ThoughtNodePublic, status_code=201)
def promote_submission_to_node(
    submission_id: int,
    node_data: ThoughtNodeCreate | None = None,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Approve a submission AND create a constellation node from it in one step."""
    sub = db.query(Submission).filter(Submission.id == submission_id).first()
    if not sub:
        raise HTTPException(status_code=404, detail="Submission not found.")

    sub.status      = SubmissionStatus.approved
    sub.reviewed_at = datetime.utcnow()

    cat = (node_data.category if node_data else None) or sub.category or "other"
    node = ThoughtNode(
        title      = (node_data.title if node_data and node_data.title else None) or sub.title or sub.content[:60],
        content    = (node_data.content if node_data and node_data.content else None) or sub.content,
        category   = cat,
        author     = sub.user.username if sub.user else "anonymous",
        position_x = node_data.position_x if node_data else round(random.uniform(0.1, 0.9), 3),
        position_y = node_data.position_y if node_data else round(random.uniform(0.1, 0.9), 3),
        node_radius= 14.0,
        hex_color  = CAT_COLORS.get(cat, "#7a7672"),
        is_base    = False,
        created_by = admin.id,
    )
    db.add(node)
    db.flush()
    sub.thought_node_id = node.id
    db.commit()
    db.refresh(node)
    return node
