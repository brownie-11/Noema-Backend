from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import ThoughtNode, ThoughtConnection
from backend.schemas import (
    ThoughtNodePublic, ThoughtNodeUpdate,
    ConnectionPublic, ConstellationResponse
)
from backend.dependencies import get_current_user, get_current_admin
from backend.models import User

router = APIRouter(prefix="/constellation", tags=["Constellation"])


@router.get("", response_model=ConstellationResponse)
def get_constellation(db: Session = Depends(get_db)):
    """
    Public endpoint — return the full constellation (all nodes + connections).
    The frontend uses this to render the living mind map.
    """
    nodes = db.query(ThoughtNode).order_by(ThoughtNode.created_at).all()
    connections = db.query(ThoughtConnection).all()
    return ConstellationResponse(
        nodes=[ThoughtNodePublic.model_validate(n) for n in nodes],
        connections=[ConnectionPublic.model_validate(c) for c in connections],
    )


@router.get("/nodes", response_model=list[ThoughtNodePublic])
def list_nodes(db: Session = Depends(get_db)):
    """Return all thought nodes."""
    return db.query(ThoughtNode).order_by(ThoughtNode.created_at).all()


@router.get("/nodes/{node_id}", response_model=ThoughtNodePublic)
def get_node(node_id: int, db: Session = Depends(get_db)):
    """Return a single node by ID."""
    node = db.query(ThoughtNode).filter(ThoughtNode.id == node_id).first()
    if not node:
        raise HTTPException(status_code=404, detail="Node not found.")
    return node


@router.patch("/nodes/{node_id}/position", response_model=ThoughtNodePublic)
def update_node_position(
    node_id: int,
    payload: ThoughtNodeUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Save dragged node position. Any authenticated user can move nodes
    (admin-only for content edits — see admin routes).
    """
    node = db.query(ThoughtNode).filter(ThoughtNode.id == node_id).first()
    if not node:
        raise HTTPException(status_code=404, detail="Node not found.")

    if payload.position_x is not None:
        node.position_x = payload.position_x
    if payload.position_y is not None:
        node.position_y = payload.position_y

    db.commit()
    db.refresh(node)
    return node


@router.get("/connections", response_model=list[ConnectionPublic])
def list_connections(db: Session = Depends(get_db)):
    """Return all thought connections."""
    return db.query(ThoughtConnection).all()
