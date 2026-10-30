"""Persistence layer: PostgreSQL on Render (DATABASE_URL) or local SQLite in development.

Tables
  projects   - one row per project; the whole project is stored as JSON (flexible schema)
  snapshots  - saved versions of a project (e.g. the schedule/budget baseline)
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone

from sqlalchemy import (JSON, Column, DateTime, ForeignKey, Integer, String, Text, create_engine,
                        delete, select)
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker


class Base(DeclarativeBase):
    pass


def _now():
    return datetime.now(timezone.utc)


class ProjectRow(Base):
    __tablename__ = "projects"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(300), nullable=False)
    industry = Column(String(120), default="")
    owner = Column(String(200), default="")
    data = Column(JSON, nullable=False)
    created_at = Column(DateTime(timezone=True), default=_now)
    updated_at = Column(DateTime(timezone=True), default=_now, onupdate=_now)


class SnapshotRow(Base):
    __tablename__ = "snapshots"
    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), index=True)
    label = Column(String(300), default="")
    note = Column(Text, default="")
    data = Column(JSON, nullable=False)
    created_at = Column(DateTime(timezone=True), default=_now)


def database_url() -> str:
    url = os.environ.get("DATABASE_URL", "").strip()
    if not url:
        os.makedirs("data", exist_ok=True)
        return "sqlite:///data/pm_studio.db"
    # Render (and Heroku) give "postgres://..." – SQLAlchemy needs "postgresql+psycopg2://"
    if url.startswith("postgres://"):
        url = "postgresql+psycopg2://" + url[len("postgres://"):]
    elif url.startswith("postgresql://"):
        url = "postgresql+psycopg2://" + url[len("postgresql://"):]
    return url


_ENGINE = None
_SESSION = None


def engine():
    global _ENGINE, _SESSION
    if _ENGINE is None:
        url = database_url()
        kwargs = {"pool_pre_ping": True}
        if url.startswith("sqlite"):
            kwargs["connect_args"] = {"check_same_thread": False}
        _ENGINE = create_engine(url, **kwargs)
        Base.metadata.create_all(_ENGINE)
        _SESSION = sessionmaker(bind=_ENGINE, expire_on_commit=False)
    return _ENGINE


def session() -> Session:
    engine()
    return _SESSION()


def backend_name() -> str:
    return "PostgreSQL" if database_url().startswith("postgresql") else "SQLite (local)"


def _clean(data: dict) -> dict:
    # guarantee JSON-serialisable content (dates, numpy numbers...)
    return json.loads(json.dumps(data, default=str))


def list_projects() -> list[dict]:
    with session() as s:
        rows = s.execute(select(ProjectRow).order_by(ProjectRow.updated_at.desc())).scalars().all()
        return [{"id": r.id, "name": r.name, "industry": r.industry, "updated_at": r.updated_at} for r in rows]


def load_project(pid: int) -> dict | None:
    with session() as s:
        r = s.get(ProjectRow, pid)
        return None if r is None else dict(r.data)


def save_project(data: dict, pid: int | None = None) -> int:
    data = _clean(data)
    meta = data.get("meta", {})
    with session() as s:
        if pid:
            r = s.get(ProjectRow, pid)
            if r is None:
                r = ProjectRow(data=data, name=meta.get("name", "Projeto"))
                s.add(r)
        else:
            r = ProjectRow(data=data, name=meta.get("name", "Projeto"))
            s.add(r)
        r.name = (meta.get("name") or "Projeto")[:300]
        r.industry = (meta.get("industry") or "")[:120]
        r.data = data
        r.updated_at = _now()
        s.commit()
        return r.id


def delete_project(pid: int) -> None:
    with session() as s:
        s.execute(delete(SnapshotRow).where(SnapshotRow.project_id == pid))
        s.execute(delete(ProjectRow).where(ProjectRow.id == pid))
        s.commit()


def add_snapshot(pid: int, label: str, data: dict, note: str = "") -> int:
    with session() as s:
        r = SnapshotRow(project_id=pid, label=label[:300], note=note, data=_clean(data))
        s.add(r)
        s.commit()
        return r.id


def list_snapshots(pid: int) -> list[dict]:
    with session() as s:
        rows = s.execute(select(SnapshotRow).where(SnapshotRow.project_id == pid)
                         .order_by(SnapshotRow.created_at.desc())).scalars().all()
        return [{"id": r.id, "label": r.label, "note": r.note, "created_at": r.created_at} for r in rows]


def load_snapshot(sid: int) -> dict | None:
    with session() as s:
        r = s.get(SnapshotRow, sid)
        return None if r is None else dict(r.data)
