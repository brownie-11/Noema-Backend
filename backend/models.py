from datetime import datetime
import enum
from sqlalchemy import (
    Column, Integer, String, Text, DateTime, Float,
    ForeignKey, Enum as SAEnum, Boolean
)
from sqlalchemy.orm import relationship
from backend.database import Base


class UserRole(str, enum.Enum):
    user  = "user"
    admin = "admin"


class SubmissionStatus(str, enum.Enum):
    pending  = "pending"
    approved = "approved"
    rejected = "rejected"


class ConnectionType(str, enum.Enum):
    contradiction        = "contradiction"
    continuation         = "continuation"
    inspiration          = "inspiration"
    emotional_resonance  = "emotional_resonance"
    existential_conflict = "existential_conflict"
    memory_link          = "memory_link"
    expansion            = "expansion"


class User(Base):
    __tablename__ = "users"

    id            = Column(Integer, primary_key=True, index=True)
    username      = Column(String(80),  unique=True, index=True, nullable=False)
    email         = Column(String(200), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role          = Column(SAEnum(UserRole), default=UserRole.user, nullable=False)
    is_active     = Column(Boolean, default=True)
    created_at    = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_login    = Column(DateTime, nullable=True)

    submissions = relationship(
        "Submission", back_populates="user", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<User id={self.id} username={self.username!r} role={self.role}>"


class Submission(Base):
    __tablename__ = "submissions"

    id              = Column(Integer, primary_key=True, index=True)
    user_id         = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    title           = Column(String(200), nullable=True)
    content         = Column(Text, nullable=False)
    category        = Column(String(80), nullable=True, default="other")
    status          = Column(SAEnum(SubmissionStatus), default=SubmissionStatus.pending, nullable=False)
    admin_note      = Column(Text, nullable=True)
    created_at      = Column(DateTime, default=datetime.utcnow, nullable=False)
    reviewed_at     = Column(DateTime, nullable=True)
    thought_node_id = Column(Integer, ForeignKey("thought_nodes.id"), nullable=True)

    user = relationship("User", back_populates="submissions")

    def __repr__(self):
        return f"<Submission id={self.id} status={self.status} user_id={self.user_id}>"


class ThoughtNode(Base):
    __tablename__ = "thought_nodes"

    id          = Column(Integer, primary_key=True, index=True)
    title       = Column(String(200), nullable=False)
    content     = Column(Text, nullable=False)
    category    = Column(String(80), nullable=False, default="other")
    author      = Column(String(200), nullable=True)
    position_x  = Column(Float, default=0.5, nullable=False)
    position_y  = Column(Float, default=0.5, nullable=False)
    node_radius = Column(Float, default=14.0, nullable=False)
    hex_color   = Column(String(20), nullable=True)
    is_base     = Column(Boolean, default=False)
    created_by  = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at  = Column(DateTime, default=datetime.utcnow, nullable=False)

    source_connections = relationship(
        "ThoughtConnection",
        foreign_keys="ThoughtConnection.source_node_id",
        back_populates="source_node",
        cascade="all, delete-orphan",
    )
    target_connections = relationship(
        "ThoughtConnection",
        foreign_keys="ThoughtConnection.target_node_id",
        back_populates="target_node",
        cascade="all, delete-orphan",
    )

    def __repr__(self):
        return f"<ThoughtNode id={self.id} title={self.title!r}>"


class ThoughtConnection(Base):
    __tablename__ = "thought_connections"

    id              = Column(Integer, primary_key=True, index=True)
    source_node_id  = Column(Integer, ForeignKey("thought_nodes.id"), nullable=False)
    target_node_id  = Column(Integer, ForeignKey("thought_nodes.id"), nullable=False)
    connection_type = Column(SAEnum(ConnectionType), nullable=False)
    created_at      = Column(DateTime, default=datetime.utcnow, nullable=False)

    source_node = relationship(
        "ThoughtNode", foreign_keys=[source_node_id], back_populates="source_connections"
    )
    target_node = relationship(
        "ThoughtNode", foreign_keys=[target_node_id], back_populates="target_connections"
    )

    def __repr__(self):
        return f"<ThoughtConnection {self.source_node_id}→{self.target_node_id} [{self.connection_type}]>"
