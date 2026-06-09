# Committing the Phase 2 Backend

This adds the working production backend the API tokens plug into: FastAPI, async
SQLAlchemy, three live connectors (CrowdStrike, Mimecast, Qualys) on a shared base
class, a risk scorer, JWT auth with RBAC, and OIDC endpoints. The dashboard is also
rewired to fetch from this API with a fallback to bundled demo data.

## Verified working
- All modules import; server boots; `/docs` live
- Local login returns a real signed JWT; bad passwords rejected (401)
- Protected endpoints enforce the bearer token
- Ingestion degrades gracefully with no tokens (reports available connectors)
- End-to-end pipeline test passes: collect → score → correlate (dc01 critical scored 88)

## What's added

```
backend/
├── README.md
├── requirements.txt
├── migrations/001_initial_schema.sql
├── src/
│   ├── config.py                 # all settings from .env
│   ├── ingestion/
│   │   ├── cas.py                # Common Alert Schema
│   │   └── connectors/
│   │       ├── base.py           # base class others extend
│   │       ├── crowdstrike.py    # live EDR connector
│   │       ├── mimecast.py       # live email connector
│   │       └── qualys.py         # live VMDR connector
│   ├── intelligence/risk_scorer.py
│   ├── db/{models,repository}.py
│   ├── auth/{service,oidc}.py    # JWT, RBAC, Entra/Okta
│   └── api/{main,deps}.py + routers/
└── tests/test_pipeline.py
```

Plus `frontend/index.html` is updated to try the live API and fall back to demo data.

## Step 1 — Unzip into your repo

Download `backend.zip`, then:

```powershell
cd "D:\ai agent projects\secureglass"
Expand-Archive -Path "C:\path\to\backend.zip" -DestinationPath . -Force
# also copy the updated dashboard
Copy-Item "C:\path\to\sentinel-glass-dashboard.html" frontend\index.html -Force
```

## Step 2 — (Optional) test the backend locally

```powershell
cd backend
python -m venv .venv; .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn src.api.main:app --reload
# visit http://127.0.0.1:8000/docs  — try POST /auth/local/login (analyst/demo)
```

## Step 3 — Commit and push

```powershell
cd "D:\ai agent projects\secureglass"
git add .
git status      # backend/ new; frontend/index.html modified; no .env, no .venv, no *.db
git commit -m "feat: Phase 2 backend — FastAPI, live connectors, risk scorer, JWT/RBAC auth, OIDC

- BaseConnector + live CrowdStrike, Mimecast, Qualys implementations
- Common Alert Schema normalisation + weighted risk scorer
- Async SQLAlchemy models + repository (Postgres, SQLite fallback)
- JWT auth with RBAC; OIDC redirect/exchange for Entra ID and Okta
- Connectors make live API calls when tokens present, skip gracefully otherwise
- Dashboard fetches live API with demo-data fallback
- End-to-end pipeline test"
git push origin main
```

## Important: keep secrets out

Before committing, confirm `.gitignore` excludes `.env`, `.venv/`, `__pycache__/`,
and `*.db`. The `git status` in Step 3 is the check — only `backend/` source and the
dashboard should appear, never a real `.env`.

## Going live with real data

1. Put real tokens in `backend/.env` (copy from `.env.example`).
2. `GET /api/v1/health` confirms which connectors are configured.
3. `POST /api/v1/ingest/run` pulls + scores + stores live alerts.
4. Deploy the API on a server (not GitHub Pages — it needs to run Python and hold
   secrets). Point the dashboard's `API_BASE` at that origin.
