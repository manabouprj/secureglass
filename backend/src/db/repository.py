"""
Repository — persistence + query helpers over the ORM.
Keeps SQL out of the API routers.
"""
from __future__ import annotations
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from .models import AlertORM
from ..ingestion.cas import CASAlert


async def upsert_alerts(session: AsyncSession, alerts: list[CASAlert]) -> int:
    count = 0
    for a in alerts:
        existing = await session.get(AlertORM, a.cas_id)
        if existing:
            continue
        session.add(AlertORM(
            cas_id=a.cas_id, source_tool=a.source_tool, source_id=a.source_id,
            vertical=a.vertical, ingested_at=a.ingested_at, event_time=a.event_time,
            severity=a.severity.value, category=a.category, title=a.title,
            description=a.description, affected_assets=a.affected_assets,
            affected_region=a.affected_region, affected_cloud=a.affected_cloud,
            mitre_tactic=a.mitre_tactic, mitre_technique=a.mitre_technique,
            iocs=a.iocs.model_dump(), risk_score=a.risk_score, status=a.status.value,
        ))
        count += 1
    await session.commit()
    return count


async def query_alerts(session: AsyncSession, *, severity: str | None = None,
                       source_tool: str | None = None, vertical: str | None = None,
                       limit: int = 200) -> list[AlertORM]:
    stmt = select(AlertORM).order_by(AlertORM.event_time.desc()).limit(limit)
    if severity:
        stmt = stmt.where(AlertORM.severity == severity)
    if source_tool:
        stmt = stmt.where(AlertORM.source_tool == source_tool)
    if vertical:
        stmt = stmt.where(AlertORM.vertical == vertical)
    return list((await session.scalars(stmt)).all())


async def severity_counts(session: AsyncSession, vertical: str | None = None) -> dict[str, int]:
    stmt = select(AlertORM.severity, func.count()).group_by(AlertORM.severity)
    if vertical:
        stmt = stmt.where(AlertORM.vertical == vertical)
    rows = await session.execute(stmt)
    return {sev: n for sev, n in rows.all()}


async def compute_posture(session: AsyncSession, vertical: str | None = None) -> dict:
    counts = await severity_counts(session, vertical)
    penalty = (min(40, counts.get("CRITICAL", 0) * 8)
               + min(20, counts.get("HIGH", 0) * 3)
               + min(15, counts.get("MEDIUM", 0) * 1))
    score = max(0, min(100, 100 - penalty))
    return {
        "overall_score": score,
        "critical_count": counts.get("CRITICAL", 0),
        "high_count": counts.get("HIGH", 0),
        "medium_count": counts.get("MEDIUM", 0),
        "low_count": counts.get("LOW", 0),
    }
