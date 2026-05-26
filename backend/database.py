import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()


def _get_database_url() -> str:
    url = os.getenv("DATABASE_URL", "").strip()

    if not url:
        return "sqlite:///./noema.db"

    # Fix ONLY if it starts with exactly postgres://
    # Do NOT touch it if it already says postgresql://
    if url.startswith("postgres://"):
        url = "postgresql://" + url[len("postgres://"):]

    return url


DATABASE_URL = _get_database_url()

print(f"[Noema] Connecting to: {DATABASE_URL[:40]}...")  # safe partial log

if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},
    )
else:
    engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    from backend import models  # noqa
    Base.metadata.create_all(bind=engine)
