from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field, validator
from backend.models import UserRole, SubmissionStatus, ConnectionType


# ── Auth Schemas ─────────────────────────────────────────────────────────────

class SignupRequest(BaseModel):
    username: str = Field(..., min_length=2, max_length=80, pattern=r"^[a-zA-Z0-9_\-\.]+$")
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)

    @validator("username")
    def username_no_spaces(cls, v):
        if " " in v:
            raise ValueError("Username cannot contain spaces")
        return v.strip()


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=1)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: "UserPublic"


class PasswordResetRequest(BaseModel):
    email: EmailStr


# ── User Schemas ─────────────────────────────────────────────────────────────

class UserPublic(BaseModel):
    id: int
    username: str
    email: str
    role: UserRole
    created_at: datetime
    last_login: Optional[datetime]

    class Config:
        from_attributes = True


class UserAdmin(UserPublic):
    is_active: bool
    submission_count: Optional[int] = 0

    class Config:
        from_attributes = True


# ── Submission Schemas ────────────────────────────────────────────────────────

class SubmissionCreate(BaseModel):
    content: str = Field(..., min_length=10, max_length=5000)
    title: Optional[str] = Field(None, max_length=200)
    category: Optional[str] = Field("other", max_length=80)


class SubmissionPublic(BaseModel):
    id: int
    title: Optional[str]
    content: str
    category: Optional[str]
    status: SubmissionStatus
    created_at: datetime
    user_id: int

    class Config:
        from_attributes = True


class SubmissionWithUser(SubmissionPublic):
    admin_note: Optional[str]
    reviewed_at: Optional[datetime]
    user: Optional[UserPublic]

    class Config:
        from_attributes = True


class SubmissionReview(BaseModel):
    note: Optional[str] = Field(None, max_length=500)


# ── Thought Node Schemas ──────────────────────────────────────────────────────

class ThoughtNodeCreate(BaseModel):
    title: str = Field(..., min_length=2, max_length=200)
    content: str = Field(..., min_length=10, max_length=5000)
    category: str = Field("other", max_length=80)
    author: Optional[str] = Field(None, max_length=200)
    position_x: float = Field(0.5, ge=0.0, le=1.0)
    position_y: float = Field(0.5, ge=0.0, le=1.0)
    node_radius: float = Field(14.0, ge=8.0, le=40.0)
    hex_color: Optional[str] = Field(None, max_length=20)


class ThoughtNodeUpdate(BaseModel):
    title: Optional[str] = Field(None, max_length=200)
    content: Optional[str] = Field(None, max_length=5000)
    category: Optional[str] = Field(None, max_length=80)
    author: Optional[str] = Field(None, max_length=200)
    position_x: Optional[float] = Field(None, ge=0.0, le=1.0)
    position_y: Optional[float] = Field(None, ge=0.0, le=1.0)
    node_radius: Optional[float] = Field(None, ge=8.0, le=40.0)
    hex_color: Optional[str] = Field(None, max_length=20)


class ThoughtNodePublic(BaseModel):
    id: int
    title: str
    content: str
    category: str
    author: Optional[str]
    position_x: float
    position_y: float
    node_radius: float
    hex_color: Optional[str]
    is_base: bool
    created_at: datetime

    class Config:
        from_attributes = True


# ── Connection Schemas ────────────────────────────────────────────────────────

class ConnectionCreate(BaseModel):
    source_node_id: int
    target_node_id: int
    connection_type: ConnectionType

    @validator("target_node_id")
    def not_self_referential(cls, v, values):
        if "source_node_id" in values and v == values["source_node_id"]:
            raise ValueError("A node cannot connect to itself")
        return v


class ConnectionPublic(BaseModel):
    id: int
    source_node_id: int
    target_node_id: int
    connection_type: ConnectionType
    created_at: datetime

    class Config:
        from_attributes = True


# ── Graph Response ────────────────────────────────────────────────────────────

class ConstellationResponse(BaseModel):
    nodes: List[ThoughtNodePublic]
    connections: List[ConnectionPublic]


# ── Generic Responses ─────────────────────────────────────────────────────────

class MessageResponse(BaseModel):
    message: str
    detail: Optional[str] = None


# Update forward ref
TokenResponse.model_rebuild()
