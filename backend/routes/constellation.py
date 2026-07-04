from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.models import ThoughtNode, ThoughtConnection, User
from backend.schemas import NodeOut, NodeUpdate, ConnectionOut, ConstellationOut
from backend.dependencies import get_current_user

router = APIRouter(prefix="/constellation", tags=["Constellation"])


@router.get("", response_model=ConstellationOut)
def get_constellation(db: Session = Depends(get_db)):
    nodes = db.query(ThoughtNode).order_by(ThoughtNode.created_at).all()
    conns = db.query(ThoughtConnection).all()
    return ConstellationOut(
        nodes=[NodeOut.model_validate(n) for n in nodes],
        connections=[ConnectionOut.model_validate(c) for c in conns],
    )


@router.get("/nodes", response_model=list[NodeOut])
def list_nodes(db: Session = Depends(get_db)):
    return db.query(ThoughtNode).order_by(ThoughtNode.created_at).all()


@router.get("/connections", response_model=list[ConnectionOut])
def list_connections(db: Session = Depends(get_db)):
    return db.query(ThoughtConnection).all()


@router.patch("/nodes/{node_id}/position", response_model=NodeOut)
def save_position(
    node_id: int,
    body:    NodeUpdate,
    user:    User = Depends(get_current_user),
    db:      Session = Depends(get_db),
):
    node = db.query(ThoughtNode).filter(ThoughtNode.id == node_id).first()
    if not node:
        raise HTTPException(404, "Node not found.")
    if body.position_x is not None:
        node.position_x = body.position_x
    if body.position_y is not None:
        node.position_y = body.position_y
    db.commit(); db.refresh(node)
    return node
