"""
Base connector — the template all 20 security-control connectors extend.

Contract:
  - is_configured() : do we have credentials?
  - fetch(since)    : pull raw alerts from the vendor since a timestamp
  - normalise(raw)  : map one raw vendor record into a CASAlert
  - collect(since)  : orchestrates fetch + normalise, returns list[CASAlert]

Connectors make LIVE calls to vendor APIs when credentials are present.
When credentials are absent, is_configured() is False and the ingestion
scheduler skips the connector (logging a warning) rather than crashing.
"""
from __future__ import annotations
import logging
from abc import ABC, abstractmethod
from datetime import datetime, timedelta, timezone
import httpx

from ..cas import CASAlert

log = logging.getLogger("connector")


class ConnectorError(Exception):
    """Raised when a connector fails to fetch or authenticate."""


class BaseConnector(ABC):
    #: short identifier, e.g. "crowdstrike"
    name: str = "base"
    #: CAS category this connector emits, e.g. "ENDPOINT"
    category: str = "UNKNOWN"

    def __init__(self, timeout: float = 30.0):
        self.timeout = timeout

    # --- to be implemented by each connector ---
    @abstractmethod
    def is_configured(self) -> bool:
        """True when required credentials are present."""

    @abstractmethod
    async def fetch(self, since: datetime) -> list[dict]:
        """Return raw vendor records since `since`."""

    @abstractmethod
    def normalise(self, raw: dict) -> CASAlert:
        """Map one raw record into a CASAlert."""

    # --- shared orchestration ---
    async def collect(self, since: datetime | None = None) -> list[CASAlert]:
        if not self.is_configured():
            log.warning("[%s] not configured — skipping (no credentials)", self.name)
            return []
        if since is None:
            since = datetime.now(timezone.utc) - timedelta(hours=24)
        try:
            raw_records = await self.fetch(since)
        except ConnectorError:
            raise
        except Exception as exc:  # noqa: BLE001
            raise ConnectorError(f"[{self.name}] fetch failed: {exc}") from exc

        alerts: list[CASAlert] = []
        for raw in raw_records:
            try:
                alerts.append(self.normalise(raw))
            except Exception as exc:  # noqa: BLE001
                log.error("[%s] normalise skipped a record: %s", self.name, exc)
        log.info("[%s] collected %d alerts", self.name, len(alerts))
        return alerts

    # --- helper: shared async HTTP client ---
    def _client(self, **kwargs) -> httpx.AsyncClient:
        return httpx.AsyncClient(timeout=self.timeout, **kwargs)
