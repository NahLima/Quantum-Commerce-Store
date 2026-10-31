"""Conexão com o banco.

Postgres por padrão (`DATABASE_URL`). Para rodar/testar sem Postgres:
    USE_SQLITE=1  -> usa SQLite local em backend/app.db
"""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

USE_SQLITE = os.getenv("USE_SQLITE", "").strip() == "1"
DATABASE_URL = os.getenv("DATABASE_URL", "")

if USE_SQLITE or not DATABASE_URL:
    DATABASE_URL = f"sqlite:///{Path(__file__).resolve().parent.parent / 'app.db'}"
    connect_args = {"check_same_thread": False}
else:
    connect_args = {}

engine = create_engine(DATABASE_URL, connect_args=connect_args, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
