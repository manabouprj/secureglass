"""
Risk Scorer — applies the weighted formula from LLD §4.1 to each CAS alert.
"""
from __future__ import annotations
from datetime import datetime, timezone
from ..ingestion.cas import CASAlert, Severity

_SEV_SCORE = {
    Severity.CRITICAL: 1.0, Severity.HIGH: 0.75,
    Severity.MEDIUM: 0.5, Severity.LOW: 0.2, Severity.INFO: 0.05,
}
_CROWN_JEWEL_HINTS = ("dc", "dc0", "domaincontroller", "paw", "swift", "scada",
                      "plc", "hmi", "sis", "emr", "pacs", "core", "treasury")


def _recency(event_time: datetime) -> float:
    now = datetime.now(timezone.utc)
    if event_time.tzinfo is None:
        event_time = event_time.replace(tzinfo=timezone.utc)
    hours = (now - event_time).total_seconds() / 3600
    if hours < 1:
        return 1.0
    if hours < 4:
        return 0.8
    if hours < 24:
        return 0.5
    return 0.2


def _asset_criticality(assets: list[str]) -> float:
    joined = " ".join(assets).lower()
    if any(h in joined for h in _CROWN_JEWEL_HINTS):
        return 1.0
    if any(k in joined for k in ("srv", "server", "db", "sql")):
        return 0.7
    return 0.4


def score_alert(alert: CASAlert, correlation_count: int = 0) -> CASAlert:
    sev = _SEV_SCORE.get(alert.severity, 0.05)
    rec = _recency(alert.event_time)
    asset = _asset_criticality(alert.affected_assets)
    corr = min(0.4, 0.2 * correlation_count)

    raw = 0.4 * sev + 0.2 * rec + 0.25 * asset + 0.15 * corr
    alert.risk_score = round(min(100.0, raw * 100), 2)
    alert.risk_score_rationale = (
        f"sev={sev:.2f} recency={rec:.2f} asset={asset:.2f} corr={corr:.2f}"
    )
    return alert


def score_batch(alerts: list[CASAlert]) -> list[CASAlert]:
    # Simple correlation: count alerts sharing an IOC IP across the batch
    ip_counts: dict[str, int] = {}
    for a in alerts:
        for ip in a.iocs.ips:
            ip_counts[ip] = ip_counts.get(ip, 0) + 1
    for a in alerts:
        corr = max((ip_counts.get(ip, 1) - 1 for ip in a.iocs.ips), default=0)
        score_alert(a, correlation_count=corr)
    return alerts
