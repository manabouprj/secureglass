"""
Database layer — async SQLAlchemy 2.0 models + session factory.
Falls back to in-memory SQLite if PostgreSQL isn't reachable, so the API
runs anywhere for the demo.
"""
from __future__ import annotations
import datetime as dt
from sqlalchemy import String, Float, DateTime, JSON, Integer
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from ..config import get_settings


class Base(DeclarativeBase):
    pass


class AlertORM(Base):
    __tablename__ = "cas_alerts"
    cas_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    source_tool: Mapped[str] = mapped_column(String(64), index=True)
    source_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    vertical: Mapped[str] = mapped_column(String(32), default="enterprise", index=True)
    ingested_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True))
    event_time: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), index=True)
    severity: Mapped[str] = mapped_column(String(16), index=True)
    category: Mapped[str] = mapped_column(String(64))
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(String, nullable=True)
    affected_assets: Mapped[list] = mapped_column(JSON, default=list)
    affected_region: Mapped[str | None] = mapped_column(String(8), nullable=True)
    affected_cloud: Mapped[str | None] = mapped_column(String(32), nullable=True)
    mitre_tactic: Mapped[str | None] = mapped_column(String(128), nullable=True)
    mitre_technique: Mapped[str | None] = mapped_column(String(16), nullable=True)
    iocs: Mapped[dict] = mapped_column(JSON, default=dict)
    risk_score: Mapped[float] = mapped_column(Float, default=0.0)
    status: Mapped[str] = mapped_column(String(32), default="NEW", index=True)


class RemediationORM(Base):
    __tablename__ = "remediations"
    remediation_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    cas_id: Mapped[str] = mapped_column(String(64), index=True)
    vertical: Mapped[str] = mapped_column(String(32))
    severity: Mapped[str] = mapped_column(String(16))
    target_tool: Mapped[str] = mapped_column(String(64))
    affected_asset: Mapped[str] = mapped_column(String(255))
    proposed_steps: Mapped[list] = mapped_column(JSON, default=list)
    impact_assessment: Mapped[str | None] = mapped_column(String, nullable=True)
    ai_confidence: Mapped[float] = mapped_column(Float, default=0.0)
    requires_cosign: Mapped[bool] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(16), default="PENDING", index=True)
    decided_by: Mapped[str | None] = mapped_column(String(128), nullable=True)
    decided_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: dt.datetime.now(dt.timezone.utc))


# --- engine / session ---
def _make_engine():
    s = get_settings()
    url = s.postgres_url
    try:
        return create_async_engine(url, pool_pre_ping=True, future=True)
    except Exception:
        # Fallback for environments without Postgres
        return create_async_engine("sqlite+aiosqlite:///:memory:", future=True)


engine = _make_engine()
SessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def init_db() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_session() -> AsyncSession:
    async with SessionLocal() as session:
        yield session
