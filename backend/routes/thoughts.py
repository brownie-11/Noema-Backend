from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime
from sqlalchemy.orm import Session
from pydantic import BaseModel

from backend.database import get_db, Base
from backend.dependencies import get_admin

router = APIRouter(prefix="/thoughts", tags=["Thoughts"])


class Thought(Base):
    __tablename__ = "thoughts"
    id         = Column(Integer, primary_key=True)
    title      = Column(String(200), nullable=False)
    category   = Column(String(80),  default="other")
    preview    = Column(Text, nullable=False)
    body       = Column(Text, nullable=False)
    author     = Column(String(200), default="William · Noema")
    published  = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)


class ThoughtOut(BaseModel):
    id:         int
    title:      str
    category:   str
    preview:    str
    body:       str
    author:     Optional[str] = "William · Noema"
    published:  bool
    created_at: datetime
    model_config = {"from_attributes": True}


class ThoughtIn(BaseModel):
    title:     str
    category:  str = "other"
    preview:   str
    body:      str
    author:    str = "William · Noema"
    published: bool = True


class ThoughtUpdate(BaseModel):
    title:     Optional[str]  = None
    category:  Optional[str]  = None
    preview:   Optional[str]  = None
    body:      Optional[str]  = None
    author:    Optional[str]  = None
    published: Optional[bool] = None


# Public — anyone can read
@router.get("", response_model=list[ThoughtOut])
def list_thoughts(
    category: Optional[str] = None,
    db: Session = Depends(get_db),
):
    q = db.query(Thought).filter(Thought.published == True)  # noqa
    if category and category != "all":
        q = q.filter(Thought.category == category)
    return q.order_by(Thought.created_at.desc()).all()


@router.get("/admin", response_model=list[ThoughtOut])
def admin_list(db: Session = Depends(get_db), admin=Depends(get_admin)):
    return db.query(Thought).order_by(Thought.created_at.desc()).all()


# Admin only — create, update, delete
@router.post("", response_model=ThoughtOut, status_code=201)
def create_thought(
    body: ThoughtIn,
    db: Session = Depends(get_db),
    admin=Depends(get_admin),
):
    now = datetime.utcnow()
    t = Thought(
        title=body.title, category=body.category,
        preview=body.preview, body=body.body,
        author=body.author, published=body.published,
        created_at=now, updated_at=now,
    )
    db.add(t); db.commit(); db.refresh(t)
    return t


@router.put("/admin/{thought_id}", response_model=ThoughtOut)
def update_thought(
    thought_id: int,
    body: ThoughtUpdate,
    db: Session = Depends(get_db),
    admin=Depends(get_admin),
):
    t = db.query(Thought).filter(Thought.id == thought_id).first()
    if not t:
        raise HTTPException(404, "Thought not found.")
    for k, v in body.model_dump(exclude_unset=True).items():
        setattr(t, k, v)
    t.updated_at = datetime.utcnow()
    db.commit(); db.refresh(t)
    return t


@router.delete("/admin/{thought_id}")
def delete_thought(
    thought_id: int,
    db: Session = Depends(get_db),
    admin=Depends(get_admin),
):
    t = db.query(Thought).filter(Thought.id == thought_id).first()
    if not t:
        raise HTTPException(404, "Thought not found.")
    db.delete(t); db.commit()
    return {"message": f"Deleted '{t.title}'"}
