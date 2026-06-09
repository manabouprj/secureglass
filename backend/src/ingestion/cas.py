"""
Common Alert Schema (CAS) — the normalised format every connector maps into.
This is the contract that lets 20 different vendors feed one dashboard.
"""
from __future__ import annotations
from datetime import datetime, timezone
from enum import Enum
from uuid import uuid4
from pydantic import BaseModel, Field


class Severity(str, Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    INFO = "INFO"


class Status(str, Enum):
    NEW = "NEW"
    IN_PROGRESS = "IN_PROGRESS"
    RESOLVED = "RESOLVED"
    SUPPRESSED = "SUPPRESSED"


class IOCs(BaseModel):
    hashes: list[str] = Field(default_factory=list)
    ips: list[str] = Field(default_factory=list)
    domains: list[str] = Field(default_factory=list)
    urls: list[str] = Field(default_factory=list)


class CASAlert(BaseModel):
    cas_id: str = Field(default_factory=lambda: str(uuid4()))
    source_tool: str
    source_id: str | None = None
    vertical: str = "enterprise"
    ingested_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    event_time: datetime
    severity: Severity
    category: str
    title: str
    description: str | None = None
    affected_assets: list[str] = Field(default_factory=list)
    affected_region: str | None = None
    affected_cloud: str | None = None
    mitre_tactic: str | None = None
    mitre_technique: str | None = None
    iocs: IOCs = Field(default_factory=IOCs)
    risk_score: float = 0.0
    risk_score_rationale: str | None = None
    status: Status = Status.NEW

    @staticmethod
    def severity_from_cvss(cvss: float) -> Severity:
        if cvss >= 9.0:
            return Severity.CRITICAL
        if cvss >= 7.0:
            return Severity.HIGH
        if cvss >= 4.0:
            return Severity.MEDIUM
        if cvss > 0:
            return Severity.LOW
        return Severity.INFO
