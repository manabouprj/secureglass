"""
Qualys VMDR connector — Vulnerability Management.
Auth: HTTP Basic (Qualys API v2). Live calls.
Docs: https://www.qualys.com/docs/qualys-api-vmpc-user-guide.pdf
Note: Qualys returns XML; we parse it into CAS records.
"""
from __future__ import annotations
from datetime import datetime, timezone
import xml.etree.ElementTree as ET
import httpx

from ..cas import CASAlert, Severity, IOCs
from .base import BaseConnector, ConnectorError
from ...config import get_settings


class QualysConnector(BaseConnector):
    name = "qualys"
    category = "VULNERABILITY"

    def __init__(self):
        super().__init__()
        s = get_settings()
        self.username = s.qualys_username
        self.password = s.qualys_password
        self.base_url = s.qualys_api_url.rstrip("/")

    def is_configured(self) -> bool:
        return bool(self.username and self.password)

    async def fetch(self, since: datetime) -> list[dict]:
        # Qualys requires this header and uses Basic auth
        headers = {"X-Requested-With": "SecureGlass"}
        auth = (self.username, self.password)
        params = {
            "action": "list",
            "detection_updated_since": since.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "show_results": "1",
            "severities": "3-5",  # medium and above
            "truncation_limit": "500",
        }
        async with self._client(auth=auth, headers=headers) as client:
            resp = await client.get(
                f"{self.base_url}/api/2.0/fo/asset/host/vm/detection/", params=params
            )
            if resp.status_code != 200:
                raise ConnectorError(f"Qualys query failed: HTTP {resp.status_code}")
            return self._parse_xml(resp.text)

    @staticmethod
    def _parse_xml(xml_text: str) -> list[dict]:
        records: list[dict] = []
        try:
            root = ET.fromstring(xml_text)
        except ET.ParseError as exc:
            raise ConnectorError(f"Qualys XML parse error: {exc}") from exc
        for host in root.iter("HOST"):
            ip = host.findtext("IP", default="")
            dns = host.findtext("DNS", default="")
            for det in host.iter("DETECTION"):
                records.append({
                    "qid": det.findtext("QID", ""),
                    "severity": det.findtext("SEVERITY", "3"),
                    "title": det.findtext("RESULTS", "") or "Qualys detection",
                    "ip": ip,
                    "dns": dns,
                    "first_found": det.findtext("FIRST_FOUND_DATETIME", ""),
                    "cvss": det.findtext("CVSS_BASE", "0"),
                })
        return records

    def normalise(self, raw: dict) -> CASAlert:
        try:
            cvss = float(raw.get("cvss") or 0)
        except ValueError:
            cvss = 0.0
        severity = CASAlert.severity_from_cvss(cvss) if cvss else self._sev_from_qualys(raw.get("severity", "3"))
        return CASAlert(
            source_tool=self.name,
            source_id=raw.get("qid"),
            event_time=raw.get("first_found") or datetime.now(timezone.utc),
            severity=severity,
            category=self.category,
            title=(raw.get("title") or "Qualys vulnerability")[:255],
            description=f"QID {raw.get('qid')} · CVSS {cvss}",
            affected_assets=[raw.get("dns") or raw.get("ip") or "unknown"],
            mitre_tactic="Initial Access",
            mitre_technique="T1190",
            iocs=IOCs(ips=[raw["ip"]] if raw.get("ip") else []),
        )

    @staticmethod
    def _sev_from_qualys(level: str) -> Severity:
        # Qualys severity 1-5 → CAS
        return {"5": Severity.CRITICAL, "4": Severity.HIGH,
                "3": Severity.MEDIUM, "2": Severity.LOW, "1": Severity.INFO}.get(level, Severity.MEDIUM)
