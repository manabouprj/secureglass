# SentinelOne-Glass — High Level Design (HLD)

**Project**: SentinelOne-Glass — Enterprise Security Intelligence Platform  
**Version**: 1.0  
**Author**: Fred (Security Architect)  
**Classification**: Internal — Architecture Reference  
**Last Updated**: June 2026

---

## 1. Executive Summary

SentinelOne-Glass is an AI-powered, single-pane-of-glass security intelligence platform designed for an enterprise organisation operating across 80 countries with multi-cloud presence (Azure, AWS, GCP). It ingests telemetry, alerts, and reports from 20+ security controls, normalises the data, and presents a unified executive and operational dashboard covering:

- Real-time Security Posture
- Risk Status and Trend Analysis
- Active/Predicted Attack Detection
- Compliance and Asset Coverage Metrics

---

## 2. Business Drivers

| Driver | Description |
|--------|-------------|
| Alert Fatigue | CIO/CISO receive fragmented daily/weekly/monthly reports from 20+ tools |
| Visibility Gap | No cross-platform correlation between CrowdStrike, Qualys, Mimecast, etc. |
| Decision Latency | Manual aggregation delays executive decisions by 12–48 hours |
| Regulatory Exposure | Multi-jurisdiction compliance (GDPR, DIFC, NCA CSF, SOC2) with no unified view |
| Threat Detection | No proactive attack prediction or early-warning capability |

---

## 3. Scope

### In Scope
- Ingestion from 20 security controls (listed in Section 6)
- AI-driven alert normalisation and risk scoring
- Executive dashboard (CIO/CISO level)
- Analyst operational dashboard
- Attack prediction engine (ML-based)
- REST API for programmatic access
- GitHub-hosted demo with synthetic data

### Out of Scope
- SOAR playbook execution
- Ticketing system integration (Phase 2)
- Mobile app (Phase 2)
- SIEM replacement

---

## 4. Architecture Principles

1. **API-First**: All integrations via vendor REST/Webhook APIs
2. **Normalisation Layer**: Common Alert Schema (CAS) for cross-tool correlation
3. **Stateless Ingestion**: Agents are ephemeral; state persists in PostgreSQL
4. **AI-Augmented**: Claude (Anthropic) for narrative summaries and risk scoring
5. **Demo-Ready**: Full synthetic data layer for GitHub-visible demo
6. **Cloud-Agnostic**: Deployable on Azure, AWS, GCP, or on-premises

---

## 5. High Level Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                        SECURITY CONTROL PLANE                       │
│  CrowdStrike │ Mimecast │ Qualys │ Palo Alto │ Zscaler │ SentinelOne │
│  Defender │ Wiz │ Salt │ Recorded Future │ Symantec DLP │ + 10 more  │
└─────────────────────┬───────────────────────────────────────────────┘
                      │ Webhooks / REST APIs / Syslog
                      ▼
┌─────────────────────────────────────────────────────────────────────┐
│                     INGESTION & NORMALISATION LAYER                  │
│         Common Alert Schema (CAS) · Source Connectors               │
│              Rate-limit handling · Retry logic                       │
└─────────────────────┬───────────────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────────────┐
│                       AI INTELLIGENCE ENGINE                         │
│  Risk Scorer │ Attack Predictor │ Narrative Generator │ Correlator  │
│                     (Claude API / Local ML)                          │
└─────────────────────┬───────────────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         DATA PERSISTENCE LAYER                       │
│             PostgreSQL (alerts, scores, posture snapshots)           │
│             Redis (real-time cache, session state)                   │
└─────────────────────┬───────────────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        PRESENTATION LAYER                            │
│          Executive Dashboard │ Analyst Dashboard │ REST API          │
│                    React + Chart.js + D3                             │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 6. Security Control Integration Matrix

| # | Control | Vendor | Data Type | Frequency |
|---|---------|--------|-----------|-----------|
| 1 | EDR | CrowdStrike Falcon | Alerts, Incidents, IOCs | Real-time |
| 2 | Email Security | Mimecast | Threat events, Blocked emails, Impersonation | Real-time |
| 3 | VMDR | Qualys | CVEs, Asset risk, Patch compliance | Daily |
| 4 | SASE/ZTNA | Zscaler / Cloudflare One | Policy violations, Blocked sessions | Real-time |
| 5 | NGFW | Palo Alto Networks | Firewall events, Threat logs | Real-time |
| 6 | CSPM | Wiz / Microsoft Defender for Cloud | Misconfigs, Cloud risk | Every 15 min |
| 7 | Asset Management | ServiceNow / Axonius | Asset inventory, Coverage gaps | Hourly |
| 8 | SOC | Internal SIEM (Sentinel) | Incidents, MTTR, SLA status | Real-time |
| 9 | API Security | Salt Security / Noname | API anomalies, Shadow APIs | Real-time |
| 10 | Digital Brand Protection | Recorded Future / ZeroFox | Phishing domains, Dark web | Hourly |
| 11 | DLP | Symantec DLP / Purview | Data exfiltration events | Real-time |
| 12 | AI Detection & Response | Vectra AI / Darktrace | Lateral movement, AI threats | Real-time |
| 13 | Identity & PAM | CyberArk / Entra ID | Privilege escalation, MFA fails | Real-time |
| 14 | Network Detection (NDR) | ExtraHop / Corelight | Network anomalies, C2 traffic | Real-time |
| 15 | Web Application Firewall | Cloudflare WAF / Azure WAF | WAF blocks, Bot attacks | Real-time |
| 16 | Cloud Workload Protection | Prisma Cloud | Container/VM threats | Real-time |
| 17 | Threat Intelligence | Recorded Future / MISP | IOCs, TTPs, Threat actors | Hourly |
| 18 | Mobile Device Management | Intune / Jamf | Non-compliant devices | Hourly |
| 19 | Backup & Recovery | Veeam / Commvault | Backup failures, Anomalies | Daily |
| 20 | Security Awareness | KnowBe4 | Phishing sim results, Training | Weekly |

---

## 7. Dashboard Modules

### 7.1 Security Posture Score
- Composite score (0–100) weighted across all 20 controls
- Trend: 7-day, 30-day, 90-day
- Breakdown by control domain (Endpoint, Cloud, Identity, Email, Network)

### 7.2 Risk Status
- Risk heat map by geography (80 countries)
- Critical/High/Medium/Low alert counts
- Top 10 risk items requiring immediate action
- SLA breach tracking

### 7.3 Attack Surface & Threat Detection
- Active incident timeline
- Attack prediction confidence score (next 24h)
- MITRE ATT&CK coverage heatmap
- IOC correlation across tools

### 7.4 Operational Metrics
- Mean Time to Detect (MTTD) / Mean Time to Respond (MTTR)
- Asset coverage percentage by region
- Vulnerability exposure score (Qualys integration)
- Compliance posture (GDPR, ISO27001, NCA CSF)

---

## 8. Data Flow

```
Vendor API → Connector → CAS Normaliser → Risk Engine → DB → Dashboard
                                              ↕
                                       Claude AI API
                                    (Narrative + Scoring)
```

---

## 9. Deployment Architecture

### Demo Mode (GitHub)
- Synthetic data generator provides realistic alerts
- No real vendor credentials required
- Runs on Node.js / Python with SQLite
- Single `docker-compose up` launch

### Production Mode
- Kubernetes deployment (AKS / EKS / GKE)
- Secrets via HashiCorp Vault or Azure Key Vault
- PostgreSQL 15 (managed)
- Redis 7 (cache)
- Reverse proxy: Nginx + Let's Encrypt

---

## 10. Security of the Platform Itself

- All API keys encrypted at rest (AES-256)
- TLS 1.3 for all inter-service communication
- RBAC: Executive / Analyst / Admin roles
- Audit logging for all dashboard access
- MFA enforced for all logins

---

## 11. Non-Functional Requirements

| NFR | Target |
|-----|--------|
| Dashboard load time | < 3 seconds |
| Alert ingestion latency | < 30 seconds from vendor |
| Uptime | 99.9% |
| Data retention | 90 days hot, 1 year cold |
| Concurrent users | 200 |
| Supported browsers | Chrome, Edge, Firefox (latest 2 versions) |
