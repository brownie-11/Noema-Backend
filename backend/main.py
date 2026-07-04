import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

Base = declarative_base()


def _url() -> str:
    raw = os.getenv("DATABASE_URL", "").strip()
    if not raw:
        return "sqlite:///./noema.db"
    if raw.startswith("postgres://"):
        raw = "postgresql://" + raw[len("postgres://"):]
    return raw


DATABASE_URL = _url()

engine = create_engine(
    DATABASE_URL,
    **({"connect_args": {"check_same_thread": False}}
       if DATABASE_URL.startswith("sqlite") else {}),
)

SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    from backend import models          # noqa — registers all core models
    from backend.routes import thoughts  # noqa — registers Thought table
    Base.metadata.create_all(bind=engine)
