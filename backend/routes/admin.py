import random
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import User, Submission, ThoughtNode, ThoughtConnection, SubmissionStatus, Role
from backend.schemas import (
    UserAdminOut, SubmissionAdminOut, NodeCreate, NodeUpdate, NodeOut,
    ConnectionCreate, ConnectionOut, ReviewIn, Msg,
)
from backend.dependencies import get_admin

router = APIRouter(prefix="/admin", tags=["Admin"])

COLORS = {
    "consciousness":"#c8a97e","existence":"#c8a07e","time":"#8bb5c8",
    "memory":"#8bb5c8","love":"#a07ec8","fear":"#c87e8a","dreams":"#7ec8a0",
    "fragment":"#8bb5c8","other":"#7a7672",
}


# ── Users ─────────────────────────────────────────────────────────────────────

@router.get("/users", response_model=list[UserAdminOut])
def list_users(
    skip:int=0, limit:int=100,
    admin:User=Depends(get_admin), db:Session=Depends(get_db),
):
    users = db.query(User).order_by(User.created_at.desc()).offset(skip).limit(limit).all()
    out = []
    for u in users:
        count = db.query(Submission).filter(Submission.user_id == u.id).count()
        x = UserAdminOut.model_validate(u)
        x.submission_count = count
        out.append(x)
    return out


@router.delete("/users/{uid}", response_model=Msg)
def deactivate_user(uid:int, admin:User=Depends(get_admin), db:Session=Depends(get_db)):
    u = db.query(User).filter(User.id==uid).first()
    if not u: raise HTTPException(404,"User not found.")
    if u.role == Role.admin: raise HTTPException(403,"Cannot deactivate another admin.")
    u.is_active = False; db.commit()
    return Msg(message=f"@{u.username} deactivated.")


# ── Submissions ───────────────────────────────────────────────────────────────

@router.get("/submissions", response_model=list[SubmissionAdminOut])
def list_submissions(
    status_filter:str|None=None, skip:int=0, limit:int=100,
    admin:User=Depends(get_admin), db:Session=Depends(get_db),
):
    q = db.query(Submission).order_by(Submission.created_at.desc())
    if status_filter:
        try: q = q.filter(Submission.status==SubmissionStatus(status_filter))
        except ValueError: raise HTTPException(400, f"Invalid status: {status_filter}")
    return q.offset(skip).limit(limit).all()


@router.post("/approve/{sid}", response_model=Msg)
def approve(sid:int, body:ReviewIn|None=None, admin:User=Depends(get_admin), db:Session=Depends(get_db)):
    s = db.query(Submission).filter(Submission.id==sid).first()
    if not s: raise HTTPException(404,"Not found.")
    s.status=SubmissionStatus.approved; s.reviewed_at=datetime.utcnow()
    if body and body.note: s.admin_note=body.note
    db.commit()
    return Msg(message=f"Submission #{sid} approved.")


@router.post("/reject/{sid}", response_model=Msg)
def reject(sid:int, body:ReviewIn|None=None, admin:User=Depends(get_admin), db:Session=Depends(get_db)):
    s = db.query(Submission).filter(Submission.id==sid).first()
    if not s: raise HTTPException(404,"Not found.")
    s.status=SubmissionStatus.rejected; s.reviewed_at=datetime.utcnow()
    if body and body.note: s.admin_note=body.note
    db.commit()
    return Msg(message=f"Submission #{sid} rejected.")


@router.delete("/submissions/{sid}", response_model=Msg)
def delete_submission(sid:int, admin:User=Depends(get_admin), db:Session=Depends(get_db)):
    s = db.query(Submission).filter(Submission.id==sid).first()
    if not s: raise HTTPException(404,"Not found.")
    db.delete(s); db.commit()
    return Msg(message=f"Submission #{sid} deleted.")


# ── Constellation ─────────────────────────────────────────────────────────────

@router.post("/create-node", response_model=NodeOut, status_code=201)
def create_node(body:NodeCreate, admin:User=Depends(get_admin), db:Session=Depends(get_db)):
    node = ThoughtNode(
        title=body.title, content=body.content, category=body.category,
        author=body.author, position_x=body.position_x, position_y=body.position_y,
        node_radius=body.node_radius,
        hex_color=body.hex_color or COLORS.get(body.category,"#7a7672"),
        is_base=False, created_by=admin.id,
    )
    db.add(node); db.commit(); db.refresh(node)
    return node


@router.patch("/nodes/{nid}", response_model=NodeOut)
def edit_node(nid:int, body:NodeUpdate, admin:User=Depends(get_admin), db:Session=Depends(get_db)):
    node = db.query(ThoughtNode).filter(ThoughtNode.id==nid).first()
    if not node: raise HTTPException(404,"Node not found.")
    for k,v in body.model_dump(exclude_unset=True).items():
        if hasattr(node,k) and k not in ("id","created_at","is_base"):
            setattr(node,k,v)
    db.commit(); db.refresh(node)
    return node


@router.delete("/nodes/{nid}", response_model=Msg)
def delete_node(nid:int, admin:User=Depends(get_admin), db:Session=Depends(get_db)):
    node = db.query(ThoughtNode).filter(ThoughtNode.id==nid).first()
    if not node: raise HTTPException(404,"Node not found.")
    if node.is_base: raise HTTPException(403,"Base nodes cannot be deleted.")
    db.delete(node); db.commit()
    return Msg(message=f"Node '{node.title}' removed.")


@router.post("/connect-nodes", response_model=ConnectionOut, status_code=201)
def connect_nodes(body:ConnectionCreate, admin:User=Depends(get_admin), db:Session=Depends(get_db)):
    src = db.query(ThoughtNode).filter(ThoughtNode.id==body.source_node_id).first()
    tgt = db.query(ThoughtNode).filter(ThoughtNode.id==body.target_node_id).first()
    if not src: raise HTTPException(404,f"Source node #{body.source_node_id} not found.")
    if not tgt: raise HTTPException(404,f"Target node #{body.target_node_id} not found.")
    dup = db.query(ThoughtConnection).filter(
        ThoughtConnection.source_node_id==body.source_node_id,
        ThoughtConnection.target_node_id==body.target_node_id,
        ThoughtConnection.connection_type==body.connection_type,
    ).first()
    if dup: raise HTTPException(409,"Connection already exists.")
    c = ThoughtConnection(
        source_node_id=body.source_node_id,
        target_node_id=body.target_node_id,
        connection_type=body.connection_type,
    )
    db.add(c); db.commit(); db.refresh(c)
    return c


@router.delete("/connections/{cid}", response_model=Msg)
def delete_connection(cid:int, admin:User=Depends(get_admin), db:Session=Depends(get_db)):
    c = db.query(ThoughtConnection).filter(ThoughtConnection.id==cid).first()
    if not c: raise HTTPException(404,"Connection not found.")
    db.delete(c); db.commit()
    return Msg(message=f"Connection #{cid} removed.")


@router.post("/promote/{sid}", response_model=NodeOut, status_code=201)
def promote(sid:int, body:NodeCreate|None=None, admin:User=Depends(get_admin), db:Session=Depends(get_db)):
    s = db.query(Submission).filter(Submission.id==sid).first()
    if not s: raise HTTPException(404,"Submission not found.")
    s.status=SubmissionStatus.approved; s.reviewed_at=datetime.utcnow()
    cat = (body.category if body else None) or s.category or "other"
    node = ThoughtNode(
        title=(body.title if body and body.title else None) or s.title or s.content[:60],
        content=(body.content if body and body.content else None) or s.content,
        category=cat,
        author=s.user.username if s.user else "anonymous",
        position_x=body.position_x if body else round(random.uniform(0.1,0.9),3),
        position_y=body.position_y if body else round(random.uniform(0.1,0.9),3),
        node_radius=14.0,
        hex_color=COLORS.get(cat,"#7a7672"),
        is_base=False, created_by=admin.id,
    )
    db.add(node); db.flush()
    s.thought_node_id=node.id
    db.commit(); db.refresh(node)
    return node
