"""Alerts, posture, and ingestion-trigger endpoints."""
from __future__ import annotations
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from ..deps import current_user
from ...db.models import get_session
from ...db import repository as repo
from ...ingestion.connectors import all_connectors, configured_connectors
from ...intelligence.risk_scorer import score_batch
from ...config import get_settings

router = APIRouter(prefix="/api/v1", tags=["alerts"])


@router.get("/health")
async def health():
    s = get_settings()
    return {"status": "ok", "connectors": s.connector_status()}


@router.get("/alerts")
async def list_alerts(
    severity: str | None = None,
    source_tool: str | None = None,
    vertical: str | None = None,
    limit: int = Query(200, le=1000),
    session: AsyncSession = Depends(get_session),
    user=Depends(current_user),
):
    rows = await repo.query_alerts(session, severity=severity,
                                   source_tool=source_tool, vertical=vertical, limit=limit)
    return [{
        "cas_id": r.cas_id, "source_tool": r.source_tool, "severity": r.severity,
        "category": r.category, "title": r.title, "affected_assets": r.affected_assets,
        "affected_region": r.affected_region, "mitre_technique": r.mitre_technique,
        "risk_score": r.risk_score, "event_time": r.event_time.isoformat(),
        "status": r.status,
    } for r in rows]


@router.get("/posture/current")
async def posture(vertical: str | None = None,
                  session: AsyncSession = Depends(get_session),
                  user=Depends(current_user)):
    return await repo.compute_posture(session, vertical)


@router.post("/ingest/run")
async def run_ingestion(session: AsyncSession = Depends(get_session),
                        user=Depends(current_user)):
    """Trigger a collection cycle across all configured connectors."""
    connectors = configured_connectors()
    if not connectors:
        return {"ingested": 0, "note": "No connectors configured. Add tokens to .env.",
                "available": [c.name for c in all_connectors()]}
    all_alerts = []
    for c in connectors:
        all_alerts.extend(await c.collect())
    score_batch(all_alerts)
    n = await repo.upsert_alerts(session, all_alerts)
    return {"ingested": n, "connectors_run": [c.name for c in connectors]}
