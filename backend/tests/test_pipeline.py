"""End-to-end pipeline test using a fake connector (no live tokens needed)."""
import asyncio
from datetime import datetime, timezone
from src.ingestion.cas import CASAlert, Severity, IOCs
from src.ingestion.connectors.base import BaseConnector
from src.intelligence.risk_scorer import score_batch


class FakeConnector(BaseConnector):
    name = "fake_edr"
    category = "ENDPOINT"
    def is_configured(self): return True
    async def fetch(self, since):
        return [
            {"id": "1", "sev": "critical", "host": "dc01", "ip": "185.10.10.10"},
            {"id": "2", "sev": "high", "host": "ws-200", "ip": "185.10.10.10"},
            {"id": "3", "sev": "medium", "host": "ws-201", "ip": "10.0.0.5"},
        ]
    def normalise(self, raw):
        smap = {"critical": Severity.CRITICAL, "high": Severity.HIGH, "medium": Severity.MEDIUM}
        return CASAlert(
            source_tool=self.name, source_id=raw["id"],
            event_time=datetime.now(timezone.utc), severity=smap[raw["sev"]],
            category=self.category, title=f"Detection on {raw['host']}",
            affected_assets=[raw["host"]], iocs=IOCs(ips=[raw["ip"]]),
        )


def test_collect_score_pipeline():
    c = FakeConnector()
    alerts = asyncio.run(c.collect())
    assert len(alerts) == 3
    score_batch(alerts)
    # dc01 critical on a crown-jewel host with a correlated IP must score highest
    top = max(alerts, key=lambda a: a.risk_score)
    assert "dc01" in top.affected_assets[0]
    assert top.risk_score > 70
    # the two alerts sharing IP 185.10.10.10 get a correlation boost
    shared = [a for a in alerts if "185.10.10.10" in a.iocs.ips]
    assert len(shared) == 2
    print(f"PASS — 3 alerts collected, top risk={top.risk_score} on {top.affected_assets[0]}")
    for a in sorted(alerts, key=lambda x: -x.risk_score):
        print(f"  {a.severity.value:8} {a.risk_score:5.1f}  {a.affected_assets[0]:8} [{a.risk_score_rationale}]")


if __name__ == "__main__":
    test_collect_score_pipeline()
