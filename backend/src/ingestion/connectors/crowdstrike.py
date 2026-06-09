"""
CrowdStrike Falcon connector — EDR.
Auth: OAuth2 client-credentials. Makes live calls to the Falcon API.
Docs: https://falcon.crowdstrike.com/documentation
"""
from __future__ import annotations
from datetime import datetime, timezone
import httpx

from ..cas import CASAlert, Severity, IOCs
from .base import BaseConnector, ConnectorError
from ...config import get_settings

_SEV_MAP = {
    "critical": Severity.CRITICAL,
    "high": Severity.HIGH,
    "medium": Severity.MEDIUM,
    "low": Severity.LOW,
    "informational": Severity.INFO,
}


class CrowdStrikeConnector(BaseConnector):
    name = "crowdstrike"
    category = "ENDPOINT"

    def __init__(self):
        super().__init__()
        s = get_settings()
        self.client_id = s.crowdstrike_client_id
        self.client_secret = s.crowdstrike_client_secret
        self.base_url = s.crowdstrike_base_url.rstrip("/")
        self._token: str | None = None

    def is_configured(self) -> bool:
        return bool(self.client_id and self.client_secret)

    async def _authenticate(self, client: httpx.AsyncClient) -> str:
        resp = await client.post(
            f"{self.base_url}/oauth2/token",
            data={"client_id": self.client_id, "client_secret": self.client_secret},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        if resp.status_code != 201:
            raise ConnectorError(f"CrowdStrike auth failed: HTTP {resp.status_code}")
        self._token = resp.json()["access_token"]
        return self._token

    async def fetch(self, since: datetime) -> list[dict]:
        async with self._client() as client:
            token = await self._authenticate(client)
            headers = {"Authorization": f"Bearer {token}"}

            # 1) Query detection IDs created since `since`
            filt = f"created_timestamp:>'{since.astimezone(timezone.utc).isoformat()}'"
            q = await client.get(
                f"{self.base_url}/detects/queries/detects/v1",
                headers=headers, params={"filter": filt, "limit": 500},
            )
            if q.status_code != 200:
                raise ConnectorError(f"CrowdStrike query failed: HTTP {q.status_code}")
            ids = q.json().get("resources", [])
            if not ids:
                return []

            # 2) Hydrate detection details
            detail = await client.post(
                f"{self.base_url}/detects/entities/summaries/GET/v1",
                headers=headers, json={"ids": ids},
            )
            if detail.status_code != 200:
                raise ConnectorError(f"CrowdStrike detail failed: HTTP {detail.status_code}")
            return detail.json().get("resources", [])

    def normalise(self, raw: dict) -> CASAlert:
        behavior = (raw.get("behaviors") or [{}])[0]
        device = raw.get("device", {})
        sev_name = (raw.get("max_severity_displayname") or "informational").lower()
        return CASAlert(
            source_tool=self.name,
            source_id=raw.get("detection_id"),
            event_time=raw.get("created_timestamp") or datetime.now(timezone.utc),
            severity=_SEV_MAP.get(sev_name, Severity.INFO),
            category=self.category,
            title=behavior.get("display_name", "CrowdStrike detection"),
            description=behavior.get("description", ""),
            affected_assets=[device.get("hostname", "unknown")],
            affected_region=device.get("country", None),
            mitre_tactic=behavior.get("tactic"),
            mitre_technique=behavior.get("technique_id"),
            iocs=IOCs(
                hashes=[h for h in [behavior.get("sha256")] if h],
                ips=[i for i in [device.get("external_ip")] if i],
            ),
        )
