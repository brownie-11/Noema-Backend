from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator
from backend.models import UserRole, SubmissionStatus, ConnectionType


class SignupRequest(BaseModel):
    username: str = Field(..., min_length=2, max_length=80, pattern=r"^[a-zA-Z0-9_\-\.]+$")
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)

    @field_validator("username")
    @classmethod
    def username_no_spaces(cls, v: str) -> str:
        if " " in v:
            raise ValueError("Username cannot contain spaces")
        return v.strip()


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=1)


class PasswordResetRequest(BaseModel):
    email: EmailStr


class UserPublic(BaseModel):
    id: int
    username: str
    email: str
    role: UserRole
    created_at: datetime
    last_login: Optional[datetime] = None
    model_config = {"from_attributes": True}


class UserAdmin(UserPublic):
    is_active: bool
    submission_count: Optional[int] = 0
    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserPublic


class SubmissionCreate(BaseModel):
    content: str = Field(..., min_length=10, max_length=5000)
    title: Optional[str] = Field(None, max_length=200)
    category: Optional[str] = Field("other", max_length=80)


class SubmissionPublic(BaseModel):
    id: int
    title: Optional[str] = None
    content: str
    category: Optional[str] = None
    status: SubmissionStatus
    created_at: datetime
    user_id: int
    model_config = {"from_attributes": True}


class SubmissionWithUser(SubmissionPublic):
    admin_note: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    user: Optional[UserPublic] = None
    model_config = {"from_attributes": True}


class SubmissionReview(BaseModel):
    note: Optional[str] = Field(None, max_length=500)


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
    author: Optional[str] = None
    position_x: float
    position_y: float
    node_radius: float
    hex_color: Optional[str] = None
    is_base: bool
    created_at: datetime
    model_config = {"from_attributes": True}


class ConnectionCreate(BaseModel):
    source_node_id: int
    target_node_id: int
    connection_type: ConnectionType

    @model_validator(mode="after")
    def not_self_referential(self) -> "ConnectionCreate":
        if self.source_node_id == self.target_node_id:
            raise ValueError("A node cannot connect to itself")
        return self


class ConnectionPublic(BaseModel):
    id: int
    source_node_id: int
    target_node_id: int
    connection_type: ConnectionType
    created_at: datetime
    model_config = {"from_attributes": True}


class ConstellationResponse(BaseModel):
    nodes: List[ThoughtNodePublic]
    connections: List[ConnectionPublic]


class MessageResponse(BaseModel):
    message: str
    detail: Optional[str] = None
