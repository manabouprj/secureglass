# SecureGlass — Phase 2 Backend

The production backend the security-control API tokens plug into. FastAPI + async
SQLAlchemy, with live connectors for CrowdStrike, Mimecast, and Qualys, a risk
scorer, JWT auth with RBAC, and OIDC (Entra ID / Okta) endpoints.

## Run locally

```bash
cd backend
pip install -r requirements.txt
cp ../.env.example .env          # add real tokens to go live
uvicorn src.api.main:app --reload
# API at http://127.0.0.1:8000  ·  interactive docs at /docs
```

Without a PostgreSQL URL it falls back to in-memory SQLite, so it runs anywhere.

## How tokens make it "go live"

1. Put real credentials in `.env` (CrowdStrike client id/secret, Mimecast, Qualys).
2. `GET /api/v1/health` shows which connectors are now configured.
3. `POST /api/v1/ingest/run` pulls real alerts, scores them, stores them.
4. `GET /api/v1/alerts` returns the live, normalised, risk-scored data.

With **no** tokens, connectors are skipped gracefully (no crash) and the endpoint
reports which connectors are available to configure.

## Architecture

```
Vendor API → Connector.fetch() → normalise() → CASAlert
          → risk_scorer.score_batch() → repository.upsert_alerts() → PostgreSQL
          → GET /api/v1/alerts → dashboard (fetch with demo fallback)
```

## Endpoints

| Endpoint | Purpose |
|----------|---------|
| `GET  /api/v1/health` | Status + which connectors are configured |
| `POST /auth/local/login` | Local login → JWT |
| `GET  /auth/providers` | Which auth methods are enabled |
| `GET  /auth/login/{provider}` | OIDC redirect (entra/okta) |
| `GET  /auth/callback/{provider}` | OIDC code exchange |
| `GET  /api/v1/alerts` | Query alerts (auth required) |
| `GET  /api/v1/posture/current` | Posture score |
| `POST /api/v1/ingest/run` | Trigger a collection cycle |

## Adding a connector

1. Subclass `BaseConnector` in `src/ingestion/connectors/`.
2. Implement `is_configured()`, `fetch()`, `normalise()`.
3. Register it in `src/ingestion/connectors/__init__.py`.

## Tests

```bash
PYTHONPATH=. python tests/test_pipeline.py
```

## Demo credentials (local auth)

`admin` / `analyst` / `exec` / `auditor` — password `demo` for all. Roles map to the
RBAC matrix in the LLD; only admin and senior_analyst can approve remediations.
