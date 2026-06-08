# 🛡️ SecureGlass — Multi-Vertical Security Intelligence Platform

**Enterprise Security · Single Pane of Glass Dashboard · AI-Powered · 5 Industry Verticals**

> A production-grade, AI-assisted security operations dashboard adaptable across five industry verticals. Ingests and correlates alerts from 20 security controls per vertical into a unified CIO/CISO-ready view — no build step, no backend required for the demo.

[![Demo](https://img.shields.io/badge/Live_Demo-Open_Dashboard-4f8bff?style=flat-square)](./frontend/index.html)
[![Verticals](https://img.shields.io/badge/Industry_Verticals-5-22d3a5?style=flat-square)](#industry-verticals)
[![Controls](https://img.shields.io/badge/Security_Controls-20_per_vertical-f59e0b?style=flat-square)](#security-controls)
[![HLD](https://img.shields.io/badge/Docs-HLD-a78bfa?style=flat-square)](./docs/HLD.md)
[![LLD](https://img.shields.io/badge/Docs-LLD-fb923c?style=flat-square)](./docs/LLD.md)

---

## 🏭 Industry Verticals

Switch between verticals using the **selector bar** directly below the navigation — all data, tools, compliance frameworks, threat actors, terminology, and executive summaries update instantly.

| Vertical | Focus | Key Threat | Accent |
|----------|-------|------------|--------|
| 🏢 **Enterprise** | Global corp, 80 countries, multi-cloud | TA505 Ransomware | Blue |
| 🏥 **Healthcare** | NHS/Hospital, EHR, Medical Devices | Hive / BlackCat PHI Exfil | Cyan |
| 🏦 **Financial Services** | Global banking, SWIFT, insurance | FIN7 BEC / Fraud | Green |
| ⚡ **Oil & Gas / Energy** | OT/ICS, SCADA, Critical Infrastructure | Sandworm ICS Sabotage | Amber |
| 🛒 **Retail & E-Commerce** | POS, Magecart, CHD, loyalty fraud | FIN6 Card Skimming | Pink |

---

## 🚀 Quick Start

```bash
# Clone the repository
git clone https://github.com/manabouprj/secureglass.git
cd secureglass

# Option 1: Open directly in browser (zero dependencies)
open frontend/index.html

# Option 2: Local HTTP server
python3 -m http.server 8080 --directory frontend
# Visit http://localhost:8080

# Option 3: Docker
docker-compose up
# Visit http://localhost:8080
```

---

## 📊 Dashboard Views

All five views update when you switch verticals:

- **Overview** — Posture ring, 30-day trend, attack prediction engine, priority alerts, regional risk heatmap, MITRE ATT&CK coverage, MTTD/MTTR trend, tool integration status, AI executive summary
- **Alert Feed** — Filterable full event feed (severity + tool) with 180+ synthetic events per vertical
- **Threat Intel** — Active threat actor profiles, IOC summary, dark web / brand monitoring
- **Compliance** — Framework-specific scorecards (8 frameworks per vertical) + 90-day trend
- **Assets** — Coverage gaps across EDR, VMDR, MDM per region/site

---

## 🔒 Security Controls (per vertical, sample)

| # | Enterprise | Healthcare | Financial | Oil & Gas | Retail |
|---|-----------|-----------|-----------|-----------|--------|
| EDR | CrowdStrike | SentinelOne | CrowdStrike | CrowdStrike | CrowdStrike |
| Email | Mimecast | Proofpoint | Defender O365 | Proofpoint | Proofpoint |
| VMDR | Qualys | Tenable.io | Qualys | Tenable OT | Qualys |
| OT/IoT | — | Claroty | — | Dragos + Claroty | — |
| Fraud | — | — | NICE Actimize | — | Forter |
| SIEM | Sentinel | Splunk | Splunk SOAR | Splunk | Splunk |
| WAF | Cloudflare | F5 | Akamai | Palo Alto ICS | Imperva |
| DLP | Symantec | Varonis | Varonis | — | Symantec |

Full 20-control mapping per vertical in [LLD.md](./docs/LLD.md)

---

## 📂 Repository Structure

```
secureglass/
├── README.md
├── docker-compose.yml
├── .env.example
├── docs/
│   ├── HLD.md                  ← High Level Design (architecture, principles)
│   └── LLD.md                  ← Low Level Design (schema, connectors, algorithms)
├── frontend/
│   └── index.html              ← Complete single-file dashboard
├── data/
│   ├── generate_demo.py        ← Synthetic data generator (700 alerts)
│   └── demo_alerts.json        ← Pre-generated demo dataset
└── src/                        ← Backend (Phase 2)
    ├── ingestion/connectors/
    ├── intelligence/
    └── api/
```

---

## 🗺️ Roadmap

### Phase 1 — Demo (This Release)
- [x] 5-vertical switchable dashboard (Enterprise, Healthcare, Financial, Energy, Retail)
- [x] Full HLD and LLD documentation
- [x] Synthetic data generator (20 tools × 5 verticals)
- [x] 5-view dashboard with vertical-aware data

### Phase 2 — Production Backend
- [ ] FastAPI + PostgreSQL backend
- [ ] Live CrowdStrike, Mimecast, Qualys connectors
- [ ] Claude AI executive summary (live)
- [ ] Kubernetes manifests (AKS / EKS / GKE)
- [ ] GitHub Actions CI/CD

### Phase 3 — Advanced
- [ ] SOAR playbook trigger integration
- [ ] Slack / Teams alert delivery
- [ ] PDF report generation (daily / weekly / monthly)
- [ ] Mobile-responsive layout
- [ ] Multi-tenant + white-label per vertical

---

## 📄 License

MIT License — Free for commercial and non-commercial use.

---

*Built for the CIO and CISO of global enterprise organisations. Designed to replace 20 fragmented security reports with one intelligent, real-time, vertically-aware view.*
