# SentinelOne-Glass — Low Level Design (LLD)

**Project**: SentinelOne-Glass  
**Version**: 1.0  
**Component**: Full Platform LLD  
**Author**: Fred (Security Architect)

---

## 1. Common Alert Schema (CAS)

Every security event from any vendor is normalised into this schema before storage:

```json
{
  "cas_id": "uuid-v4",
  "source_tool": "crowdstrike|mimecast|qualys|...",
  "source_id": "vendor-native-alert-id",
  "ingested_at": "ISO8601",
  "event_time": "ISO8601",
  "severity": "CRITICAL|HIGH|MEDIUM|LOW|INFO",
  "category": "ENDPOINT|EMAIL|VULNERABILITY|NETWORK|CLOUD|IDENTITY|DLP|API|BRAND|AI_THREAT",
  "title": "string (max 255)",
  "description": "string",
  "affected_assets": ["hostname", "ip", "user@domain"],
  "affected_region": "ISO 3166-1 alpha-2",
  "affected_cloud": "azure|aws|gcp|on-prem|saas",
  "mitre_tactic": "string",
  "mitre_technique": "T1234",
  "iocs": {
    "hashes": [],
    "ips": [],
    "domains": [],
    "urls": []
  },
  "risk_score": 0.0,
  "risk_score_rationale": "string",
  "status": "NEW|IN_PROGRESS|RESOLVED|SUPPRESSED",
  "raw_payload": {}
}
```

---

## 2. Database Schema (PostgreSQL)

```sql
-- Core alert table
CREATE TABLE cas_alerts (
    cas_id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_tool     VARCHAR(64) NOT NULL,
    source_id       VARCHAR(255),
    ingested_at     TIMESTAMPTZ DEFAULT NOW(),
    event_time      TIMESTAMPTZ NOT NULL,
    severity        VARCHAR(16) CHECK (severity IN ('CRITICAL','HIGH','MEDIUM','LOW','INFO')),
    category        VARCHAR(64),
    title           VARCHAR(255) NOT NULL,
    description     TEXT,
    affected_region VARCHAR(8),
    affected_cloud  VARCHAR(32),
    mitre_tactic    VARCHAR(128),
    mitre_technique VARCHAR(16),
    risk_score      NUMERIC(5,2),
    status          VARCHAR(32) DEFAULT 'NEW',
    raw_payload     JSONB,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- Asset inventory (Axonius / ServiceNow feed)
CREATE TABLE assets (
    asset_id        UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    hostname        VARCHAR(255),
    ip_address      INET,
    asset_type      VARCHAR(64),   -- workstation, server, container, cloud-vm
    owner_team      VARCHAR(128),
    region          VARCHAR(8),
    cloud_provider  VARCHAR(32),
    edr_enrolled    BOOLEAN DEFAULT FALSE,
    vuln_scanned    BOOLEAN DEFAULT FALSE,
    last_seen       TIMESTAMPTZ,
    risk_score      NUMERIC(5,2),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

-- Posture snapshot (hourly aggregation)
CREATE TABLE posture_snapshots (
    snapshot_id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    snapshot_time       TIMESTAMPTZ DEFAULT NOW(),
    overall_score       NUMERIC(5,2),
    endpoint_score      NUMERIC(5,2),
    cloud_score         NUMERIC(5,2),
    identity_score      NUMERIC(5,2),
    email_score         NUMERIC(5,2),
    network_score       NUMERIC(5,2),
    vulnerability_score NUMERIC(5,2),
    critical_count      INT DEFAULT 0,
    high_count          INT DEFAULT 0,
    medium_count        INT DEFAULT 0,
    low_count           INT DEFAULT 0,
    active_incidents    INT DEFAULT 0,
    mttd_minutes        NUMERIC(8,2),
    mttr_minutes        NUMERIC(8,2)
);

-- Indexes
CREATE INDEX idx_cas_severity ON cas_alerts(severity);
CREATE INDEX idx_cas_source ON cas_alerts(source_tool);
CREATE INDEX idx_cas_event_time ON cas_alerts(event_time DESC);
CREATE INDEX idx_cas_region ON cas_alerts(affected_region);
CREATE INDEX idx_cas_status ON cas_alerts(status);
CREATE INDEX idx_assets_region ON assets(region);
CREATE INDEX idx_posture_time ON posture_snapshots(snapshot_time DESC);
```

---

## 3. Connector Specifications

### 3.1 CrowdStrike Falcon Connector

**Authentication**: OAuth2 Client Credentials  
**Endpoints Used**:
- `GET /incidents/queries/incidents/v1` — Active incidents
- `GET /detects/queries/detects/v1` — Detections
- `GET /intel/combined/indicators/v1` — Threat intel IOCs
- `POST /oauth2/token` — Token refresh

**Polling interval**: 60 seconds (real-time streaming preferred via Falcon Data Replicator)

```python
class CrowdStrikeConnector:
    def __init__(self, client_id: str, client_secret: str, base_url: str):
        self.client_id = client_id
        self.client_secret = client_secret
        self.base_url = base_url
        self._token = None
        self._token_expiry = None

    def get_detections(self, last_seen: datetime) -> list[dict]:
        """Fetch detections since last_seen, return normalised CAS list"""
        ...

    def normalise(self, raw: dict) -> dict:
        """Map CrowdStrike detection to CAS"""
        severity_map = {
            'Critical': 'CRITICAL', 'High': 'HIGH',
            'Medium': 'MEDIUM', 'Low': 'LOW', 'Informational': 'INFO'
        }
        return {
            'source_tool': 'crowdstrike',
            'source_id': raw.get('detection_id'),
            'event_time': raw.get('created_timestamp'),
            'severity': severity_map.get(raw.get('max_severity_displayname'), 'INFO'),
            'category': 'ENDPOINT',
            'title': raw.get('behaviors', [{}])[0].get('display_name', 'Unknown'),
            'description': raw.get('behaviors', [{}])[0].get('description', ''),
            'affected_assets': [raw.get('device', {}).get('hostname', '')],
            'mitre_tactic': raw.get('behaviors', [{}])[0].get('tactic', ''),
            'mitre_technique': raw.get('behaviors', [{}])[0].get('technique_id', ''),
            'iocs': {
                'hashes': [raw.get('behaviors', [{}])[0].get('sha256', '')],
                'ips': [raw.get('device', {}).get('external_ip', '')],
                'domains': [],
                'urls': []
            }
        }
```

### 3.2 Mimecast Email Security Connector

**Authentication**: OAuth2 (Mimecast Cloud API v2)  
**Endpoints Used**:
- `POST /api/ttp/url/get-logs` — URL threat logs
- `POST /api/ttp/attachment/get-logs` — Attachment threat logs
- `POST /api/ttp/impersonation/get-logs` — Impersonation events
- `POST /api/awareness-training/phishing/get-campaign-summary` — Phishing sim

**Polling interval**: 5 minutes

**Normalisation mapping**:
```
mimecast.actionTriggered = block → severity HIGH
mimecast.definition = Spam → severity LOW
mimecast.definition = Malware → severity CRITICAL
mimecast.definition = Impersonation → severity HIGH
```

### 3.3 Qualys VMDR Connector

**Authentication**: Basic Auth (API v2) or API Token  
**Endpoints Used**:
- `GET /api/2.0/fo/asset/host/?action=list` — Host assets
- `GET /api/2.0/fo/scan/?action=list` — Scan results
- `POST /api/2.0/fo/report/?action=launch` — Launch report
- `GET /qps/rest/2.0/search/was/wasscan` — Web app scan data

**Polling interval**: 4 hours (scan-result driven)

**Risk Score Mapping (CVSS to CAS severity)**:
```
CVSS 9.0 – 10.0 → CRITICAL
CVSS 7.0 – 8.9  → HIGH
CVSS 4.0 – 6.9  → MEDIUM
CVSS 0.1 – 3.9  → LOW
```

---

## 4. AI Intelligence Engine

### 4.1 Risk Scorer

The risk scorer applies a weighted formula across alert attributes:

```
risk_score = (
    severity_weight × severity_score +
    age_weight × recency_score +
    asset_weight × asset_criticality +
    context_weight × correlation_boost
)

Where:
  severity_score: CRITICAL=1.0, HIGH=0.75, MEDIUM=0.5, LOW=0.2
  recency_score: 1.0 if < 1h, 0.8 if < 4h, 0.5 if < 24h, 0.2 if > 24h
  asset_criticality: 1.0 if DC/PAW/Crown jewel, 0.7 if server, 0.4 if workstation
  correlation_boost: +0.2 per correlated alert from another tool (max 0.4)
  Weights: severity=0.4, age=0.2, asset=0.25, context=0.15
```

### 4.2 Attack Prediction Engine

A lightweight ML model (Random Forest + LSTM hybrid) trained on:
- Intra-day alert velocity per category
- Alert-to-incident conversion rate
- IOC overlap with threat intelligence feeds
- Time-based patterns (weekends, holidays, shift gaps)

Outputs:
- `attack_probability_24h`: float 0.0–1.0
- `predicted_vector`: "Ransomware | Phishing | Lateral Movement | Exfiltration | ..."
- `confidence`: "HIGH | MEDIUM | LOW"
- `supporting_evidence`: list of CAS alert IDs driving the prediction

### 4.3 Claude AI Narrative Generator

Claude is invoked for:
1. **Executive Summary**: Converts raw posture snapshot to 3-paragraph board-ready briefing
2. **Alert Triage Assist**: Explains complex correlated incidents in plain English
3. **Risk Narrative**: Synthesises top 5 risks into actionable recommendations

```python
def generate_executive_summary(snapshot: dict, top_alerts: list) -> str:
    prompt = f"""
    You are a CISO writing a brief for the CIO. Today's security posture score is 
    {snapshot['overall_score']}/100. There are {snapshot['critical_count']} critical 
    and {snapshot['high_count']} high severity alerts. The top incidents are:
    {json.dumps(top_alerts, indent=2)}
    
    Write a 3-paragraph executive summary: 
    1. Current status (2-3 sentences)
    2. Key risks requiring attention (2-3 sentences) 
    3. Recommended actions (2-3 sentences)
    Keep it under 200 words. No jargon.
    """
    # Call Claude API
    ...
```

---

## 5. Posture Score Algorithm

The overall posture score (0–100) is computed hourly:

```
posture_score = 100 - penalty

Where penalty is the sum of:
  - critical_alerts × 8 (cap at 40)
  - high_alerts × 3 (cap at 20)
  - medium_alerts × 1 (cap at 15)
  - coverage_gap_pct × 0.25 (assets without EDR/VMDR scan)
  - overdue_patches × 0.5 (cap at 10)
  - sla_breaches × 2 (cap at 10)
  - compliance_failures × 1 (cap at 5)

Each domain score uses same algorithm on filtered subset.
Score floored at 0, capped at 100.
```

---

## 6. API Specification

```
GET  /api/v1/posture/current          → PostureSnapshot
GET  /api/v1/posture/trend?days=30    → []PostureSnapshot
GET  /api/v1/alerts?severity=CRITICAL → []CASAlert
GET  /api/v1/alerts/:id               → CASAlert
GET  /api/v1/assets/coverage          → CoverageReport
GET  /api/v1/attack/prediction        → AttackPrediction
GET  /api/v1/regions/heatmap          → []RegionRisk
GET  /api/v1/summary/executive        → ExecutiveSummary (AI-generated)
POST /api/v1/ingest/:source           → 200 OK (webhook receiver)
```

---

## 7. Synthetic Data Generator

For the GitHub demo, `data/generate_demo.py` creates:

- 500 CrowdStrike alerts (30-day window, realistic distribution)
- 200 Mimecast email threat events
- 150 Qualys vulnerability findings
- 80 CSPM misconfigurations
- 60 DLP events
- 40 API security anomalies
- 30 identity/PAM alerts
- 20 WAF events
- 15 digital brand protection hits
- 10 AI-detected anomalies

Distribution: 5% CRITICAL, 15% HIGH, 40% MEDIUM, 40% LOW  
Geography: weighted to UAE, UK, US, DE, SG, ZA, BR, IN

---

## 8. File / Folder Structure

```
sentinel-one-glass/
├── README.md
├── docker-compose.yml
├── .env.example
├── docs/
│   ├── HLD.md
│   ├── LLD.md
│   └── architecture-diagram.png
├── src/
│   ├── ingestion/
│   │   ├── connectors/
│   │   │   ├── crowdstrike.py
│   │   │   ├── mimecast.py
│   │   │   ├── qualys.py
│   │   │   └── base_connector.py
│   │   └── normaliser.py
│   ├── intelligence/
│   │   ├── risk_scorer.py
│   │   ├── attack_predictor.py
│   │   └── claude_narrator.py
│   ├── api/
│   │   ├── main.py (FastAPI)
│   │   └── routers/
│   └── scheduler/
│       └── jobs.py
├── frontend/
│   ├── index.html
│   ├── dashboard.js
│   └── styles.css
├── data/
│   ├── generate_demo.py
│   └── demo_alerts.json
└── migrations/
    └── 001_initial_schema.sql
```

---

## 9. RBAC Matrix

| Role | Posture Dashboard | Alert Details | Raw Payloads | Admin Settings |
|------|-------------------|---------------|--------------|----------------|
| Executive (CIO/CISO) | ✅ Full | Summary only | ❌ | ❌ |
| Senior Analyst | ✅ Full | ✅ Full | ✅ | ❌ |
| Analyst | ✅ Full | ✅ Own alerts | ❌ | ❌ |
| Admin | ✅ Full | ✅ Full | ✅ | ✅ |
| Read-Only (Audit) | ✅ Full | Summary only | ❌ | ❌ |

---

## 10. Technology Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React 18, Chart.js 4, D3 v7, Tailwind CSS |
| API | Python 3.12 / FastAPI |
| AI Engine | Anthropic Claude API (claude-sonnet-4) |
| Database | PostgreSQL 15 |
| Cache | Redis 7 |
| Task Queue | Celery + Redis |
| Container | Docker / Docker Compose |
| Orchestration (prod) | Kubernetes (AKS/EKS/GKE) |
| Secrets (prod) | HashiCorp Vault / Azure Key Vault |
| CI/CD | GitHub Actions |
