"""SQLAlchemy engine and session setup."""

from __future__ import annotations

from collections.abc import Generator

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import Session, sessionmaker

from .config import settings
from .models import Base

connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}
engine = create_engine(settings.database_url, connect_args=connect_args)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)


def init_db() -> None:
    Base.metadata.create_all(bind=engine)
    if settings.database_url.startswith("sqlite"):
        _add_compatibility_columns()


def _add_compatibility_columns() -> None:
    """Add columns introduced after the original prototype schema."""

    additions = {
        "merchants": {
            "preferred_language": "VARCHAR(5) NOT NULL DEFAULT 'en'",
            "scenario": "VARCHAR(60) NOT NULL DEFAULT 'stable'",
        },
        "payments": {
            "due_date": "DATE",
            "status": "VARCHAR(20) NOT NULL DEFAULT 'paid'",
            "days_late": "INTEGER NOT NULL DEFAULT 0",
        },
        "alerts": {
            "action_id": "INTEGER",
        },
    }
    existing = inspect(engine)
    with engine.begin() as connection:
        for table, columns in additions.items():
            names = {column["name"] for column in existing.get_columns(table)}
            for name, definition in columns.items():
                if name not in names:
                    connection.execute(text(f'ALTER TABLE "{table}" ADD COLUMN "{name}" {definition}'))


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
