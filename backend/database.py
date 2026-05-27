from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from backend.config import settings

Base = declarative_base()


def _make_engine():
    url = settings.DATABASE_URL
    print(f"[Noema] Connecting to DB: {url[:60]}...")
    if url.startswith("sqlite"):
        return create_engine(
            url,
            connect_args={"check_same_thread": False},
            echo=settings.DEBUG,
        )
    return create_engine(
        url,
        pool_pre_ping=True,     # detects stale connections on Railway
        pool_recycle=300,
        echo=settings.DEBUG,
    )


engine = _make_engine()
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
