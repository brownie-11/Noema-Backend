from datetime import datetime
import enum
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, Float, ForeignKey, Enum as SAEnum
from sqlalchemy.orm import relationship
from backend.database import Base


class Role(str, enum.Enum):
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

    id            = Column(Integer, primary_key=True)
    username      = Column(String(80),  unique=True, nullable=False, index=True)
    email         = Column(String(200), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    role          = Column(SAEnum(Role), default=Role.user, nullable=False)
    is_active     = Column(Boolean, default=True)
    created_at    = Column(DateTime, default=datetime.utcnow)
    last_login    = Column(DateTime, nullable=True)

    submissions = relationship("Submission", back_populates="user", cascade="all, delete-orphan")


class Submission(Base):
    __tablename__ = "submissions"

    id              = Column(Integer, primary_key=True)
    user_id         = Column(Integer, ForeignKey("users.id"), nullable=False)
    title           = Column(String(200), nullable=True)
    content         = Column(Text, nullable=False)
    category        = Column(String(80), default="other")
    status          = Column(SAEnum(SubmissionStatus), default=SubmissionStatus.pending)
    admin_note      = Column(Text, nullable=True)
    created_at      = Column(DateTime, default=datetime.utcnow)
    reviewed_at     = Column(DateTime, nullable=True)
    thought_node_id = Column(Integer, ForeignKey("thought_nodes.id"), nullable=True)

    user = relationship("User", back_populates="submissions")


class ThoughtNode(Base):
    __tablename__ = "thought_nodes"

    id          = Column(Integer, primary_key=True)
    title       = Column(String(200), nullable=False)
    content     = Column(Text, nullable=False)
    category    = Column(String(80), default="other")
    author      = Column(String(200), nullable=True)
    position_x  = Column(Float, default=0.5)
    position_y  = Column(Float, default=0.5)
    node_radius = Column(Float, default=14.0)
    hex_color   = Column(String(20), nullable=True)
    is_base     = Column(Boolean, default=False)
    created_by  = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at  = Column(DateTime, default=datetime.utcnow)

    source_connections = relationship(
        "ThoughtConnection", foreign_keys="ThoughtConnection.source_node_id",
        back_populates="source_node", cascade="all, delete-orphan",
    )
    target_connections = relationship(
        "ThoughtConnection", foreign_keys="ThoughtConnection.target_node_id",
        back_populates="target_node", cascade="all, delete-orphan",
    )


class ThoughtConnection(Base):
    __tablename__ = "thought_connections"

    id              = Column(Integer, primary_key=True)
    source_node_id  = Column(Integer, ForeignKey("thought_nodes.id"), nullable=False)
    target_node_id  = Column(Integer, ForeignKey("thought_nodes.id"), nullable=False)
    connection_type = Column(SAEnum(ConnectionType), nullable=False)
    created_at      = Column(DateTime, default=datetime.utcnow)

    source_node = relationship("ThoughtNode", foreign_keys=[source_node_id], back_populates="source_connections")
    target_node = relationship("ThoughtNode", foreign_keys=[target_node_id], back_populates="target_connections")
