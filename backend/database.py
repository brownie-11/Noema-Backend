import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()


def _get_database_url() -> str:
    """
    Get and fix the database URL from environment.
    Railway gives postgres:// but SQLAlchemy needs postgresql://
    Falls back to local SQLite if nothing is set.
    """
    url = os.getenv("DATABASE_URL", "")

    if not url:
        # No env variable at all — use local SQLite
        url = "sqlite:///./noema.db"

    if url.startswith("postgres://"):
        # Railway uses the old postgres:// prefix — fix it
        url = url.replace("postgres://", "postgresql://", 1)

    return url


DATABASE_URL = _get_database_url()

# Build engine — SQLite needs check_same_thread=False, PostgreSQL doesn't
# NEW
import os

def _make_engine():
    url = settings.DATABASE_URL or ""
    # PostgreSQL from Railway comes as postgres:// — SQLAlchemy needs postgresql://
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)
    kwargs = {}
    if url.startswith("sqlite"):
        kwargs["connect_args"] = {"check_same_thread": False}
    return create_engine(url, echo=settings.DEBUG, **kwargs)

engine = _make_engine()
else:
    engine = create_engine(
        DATABASE_URL,
        echo=False,
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    from backend import models  # noqa — registers all models
    Base.metadata.create_all(bind=engine)
