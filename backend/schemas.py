from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator
from backend.models import Role, SubmissionStatus, ConnectionType


# ── Auth ──────────────────────────────────────────────────────────────────────

class SignupIn(BaseModel):
    username: str = Field(..., min_length=2, max_length=80, pattern=r"^[a-zA-Z0-9_\-\.]+$")
    email:    EmailStr
    password: str = Field(..., min_length=8)

    @field_validator("username")
    @classmethod
    def no_spaces(cls, v: str) -> str:
        return v.strip()


class LoginIn(BaseModel):
    email:    EmailStr
    password: str = Field(..., min_length=1)


class UserOut(BaseModel):
    id:         int
    username:   str
    email:      str
    role:       Role
    created_at: datetime
    last_login: Optional[datetime] = None
    model_config = {"from_attributes": True}


class TokenOut(BaseModel):
    access_token: str
    token_type:   str = "bearer"
    user:         UserOut


class UserAdminOut(UserOut):
    is_active:        bool
    submission_count: int = 0
    model_config = {"from_attributes": True}


# ── Submissions ───────────────────────────────────────────────────────────────

class SubmissionIn(BaseModel):
    content:  str = Field(..., min_length=10, max_length=5000)
    title:    Optional[str] = Field(None, max_length=200)
    category: Optional[str] = Field("other", max_length=80)


class SubmissionOut(BaseModel):
    id:         int
    user_id:    int
    title:      Optional[str] = None
    content:    str
    category:   Optional[str] = None
    status:     SubmissionStatus
    created_at: datetime
    model_config = {"from_attributes": True}


class SubmissionAdminOut(SubmissionOut):
    admin_note:  Optional[str] = None
    reviewed_at: Optional[datetime] = None
    user:        Optional[UserOut] = None
    model_config = {"from_attributes": True}


class ReviewIn(BaseModel):
    note: Optional[str] = Field(None, max_length=500)


# ── Constellation ─────────────────────────────────────────────────────────────

class NodeCreate(BaseModel):
    title:      str   = Field(..., min_length=2, max_length=200)
    content:    str   = Field(..., min_length=10, max_length=5000)
    category:   str   = Field("other", max_length=80)
    author:     Optional[str] = None
    position_x: float = Field(0.5, ge=0.0, le=1.0)
    position_y: float = Field(0.5, ge=0.0, le=1.0)
    node_radius:float = Field(14.0, ge=8.0, le=40.0)
    hex_color:  Optional[str] = None


class NodeUpdate(BaseModel):
    title:      Optional[str]   = None
    content:    Optional[str]   = None
    category:   Optional[str]   = None
    author:     Optional[str]   = None
    position_x: Optional[float] = Field(None, ge=0.0, le=1.0)
    position_y: Optional[float] = Field(None, ge=0.0, le=1.0)
    node_radius:Optional[float] = Field(None, ge=8.0, le=40.0)
    hex_color:  Optional[str]   = None


class NodeOut(BaseModel):
    id:          int
    title:       str
    content:     str
    category:    str
    author:      Optional[str] = None
    position_x:  float
    position_y:  float
    node_radius: float
    hex_color:   Optional[str] = None
    is_base:     bool
    created_at:  datetime
    model_config = {"from_attributes": True}


class ConnectionCreate(BaseModel):
    source_node_id:  int
    target_node_id:  int
    connection_type: ConnectionType

    @model_validator(mode="after")
    def no_self_loop(self):
        if self.source_node_id == self.target_node_id:
            raise ValueError("A node cannot connect to itself")
        return self


class ConnectionOut(BaseModel):
    id:              int
    source_node_id:  int
    target_node_id:  int
    connection_type: ConnectionType
    created_at:      datetime
    model_config = {"from_attributes": True}


class ConstellationOut(BaseModel):
    nodes:       List[NodeOut]
    connections: List[ConnectionOut]


# ── Generic ───────────────────────────────────────────────────────────────────

class Msg(BaseModel):
    message: str
    detail:  Optional[str] = None
