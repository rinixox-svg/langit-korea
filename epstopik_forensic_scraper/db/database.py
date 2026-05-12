from sqlmodel import SQLModel, Session, create_engine
from pathlib import Path
from config.settings import settings


_engine = None


def get_engine():
    global _engine
    if _engine is None:
        db_path = settings.ARTIFACTS_DIR / "provenance.db"
        db_path.parent.mkdir(parents=True, exist_ok=True)
        _engine = create_engine(
            settings.DATABASE_URL,
            echo=False,
            connect_args={"check_same_thread": False},
        )
    return _engine


def init_db():
    from . import models as _  # noqa: F401 — register models before create_all
    engine = get_engine()
    SQLModel.metadata.create_all(engine)
    return engine


def get_session() -> Session:
    return Session(get_engine())
