"""
Mimecast connector — Email Security.
Auth: OAuth2 client-credentials (Mimecast API 2.0). Live calls.
Docs: https://developer.services.mimecast.com
"""
from __future__ import annotations
from datetime import datetime, timezone
import httpx

from ..cas import CASAlert, Severity, IOCs
from .base import BaseConnector, ConnectorError
from ...config import get_settings

# Mimecast TTP verdicts → CAS severity
_DEF_MAP = {
    "malware": Severity.CRITICAL,
    "impersonation": Severity.HIGH,
    "malicious": Severity.HIGH,
    "spam": Severity.LOW,
}


class MimecastConnector(BaseConnector):
    name = "mimecast"
    category = "EMAIL"

    def __init__(self):
        super().__init__()
        s = get_settings()
        self.client_id = s.mimecast_client_id
        self.client_secret = s.mimecast_client_secret
        self.base_url = s.mimecast_base_url.rstrip("/")
        self._token: str | None = None

    def is_configured(self) -> bool:
        return bool(self.client_id and self.client_secret)

    async def _authenticate(self, client: httpx.AsyncClient) -> str:
        resp = await client.post(
            f"{self.base_url}/oauth/token",
            data={
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "grant_type": "client_credentials",
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        if resp.status_code != 200:
            raise ConnectorError(f"Mimecast auth failed: HTTP {resp.status_code}")
        self._token = resp.json()["access_token"]
        return self._token

    async def fetch(self, since: datetime) -> list[dict]:
        async with self._client() as client:
            token = await self._authenticate(client)
            headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
            payload = {
                "data": [{
                    "from": since.astimezone(timezone.utc).isoformat(),
                    "to": datetime.now(timezone.utc).isoformat(),
                }]
            }
            records: list[dict] = []
            for kind in ("url", "attachment", "impersonation"):
                resp = await client.post(
                    f"{self.base_url}/ttp/{kind}/get-logs",
                    headers=headers, json=payload,
                )
                if resp.status_code != 200:
                    raise ConnectorError(f"Mimecast {kind} logs failed: HTTP {resp.status_code}")
                body = resp.json()
                for block in body.get("data", []):
                    for item in block.get(f"{kind}Logs", block.get("logs", [])):
                        item["_kind"] = kind
                        records.append(item)
            return records

    def normalise(self, raw: dict) -> CASAlert:
        definition = (raw.get("definition") or raw.get("action") or "malicious").lower()
        severity = _DEF_MAP.get(definition, Severity.MEDIUM)
        kind = raw.get("_kind", "email")
        return CASAlert(
            source_tool=self.name,
            source_id=raw.get("id") or raw.get("messageId"),
            event_time=raw.get("date") or datetime.now(timezone.utc),
            severity=severity,
            category=self.category,
            title=f"Mimecast {kind} threat: {definition}",
            description=raw.get("subject", ""),
            affected_assets=[raw.get("recipientAddress", raw.get("toAddress", "unknown"))],
            mitre_tactic="Initial Access",
            mitre_technique="T1566",
            iocs=IOCs(
                urls=[u for u in [raw.get("url")] if u],
                hashes=[h for h in [raw.get("fileHash")] if h],
            ),
        )
