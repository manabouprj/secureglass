-- SecureGlass initial schema (PostgreSQL). The ORM auto-creates these;
-- this file documents the canonical production DDL.

CREATE TABLE IF NOT EXISTS cas_alerts (
    cas_id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_tool     VARCHAR(64) NOT NULL,
    source_id       VARCHAR(255),
    vertical        VARCHAR(32) DEFAULT 'enterprise',
    ingested_at     TIMESTAMPTZ DEFAULT NOW(),
    event_time      TIMESTAMPTZ NOT NULL,
    severity        VARCHAR(16) CHECK (severity IN ('CRITICAL','HIGH','MEDIUM','LOW','INFO')),
    category        VARCHAR(64),
    title           VARCHAR(255) NOT NULL,
    description     TEXT,
    affected_assets JSONB,
    affected_region VARCHAR(8),
    affected_cloud  VARCHAR(32),
    mitre_tactic    VARCHAR(128),
    mitre_technique VARCHAR(16),
    iocs            JSONB,
    risk_score      NUMERIC(5,2),
    status          VARCHAR(32) DEFAULT 'NEW'
);
CREATE INDEX IF NOT EXISTS idx_cas_severity ON cas_alerts(severity);
CREATE INDEX IF NOT EXISTS idx_cas_source   ON cas_alerts(source_tool);
CREATE INDEX IF NOT EXISTS idx_cas_event    ON cas_alerts(event_time DESC);
CREATE INDEX IF NOT EXISTS idx_cas_vertical ON cas_alerts(vertical);

CREATE TABLE IF NOT EXISTS remediations (
    remediation_id   UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    cas_id           UUID REFERENCES cas_alerts(cas_id),
    vertical         VARCHAR(32),
    severity         VARCHAR(16),
    target_tool      VARCHAR(64),
    affected_asset   VARCHAR(255),
    proposed_steps   JSONB,
    impact_assessment TEXT,
    ai_confidence    NUMERIC(5,2),
    requires_cosign  BOOLEAN DEFAULT FALSE,
    status           VARCHAR(16) DEFAULT 'PENDING'
                       CHECK (status IN ('PENDING','APPROVED','REJECTED','DEFERRED')),
    decided_by       VARCHAR(128),
    decided_at       TIMESTAMPTZ,
    created_at       TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_rem_status ON remediations(status);

CREATE TABLE IF NOT EXISTS users (
    user_id        UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email          VARCHAR(255) UNIQUE NOT NULL,
    display_name   VARCHAR(255),
    auth_provider  VARCHAR(32) NOT NULL,
    role           VARCHAR(32) NOT NULL DEFAULT 'read_only',
    password_hash  TEXT,
    totp_secret    TEXT,
    mfa_enabled    BOOLEAN DEFAULT TRUE,
    is_active      BOOLEAN DEFAULT TRUE,
    last_login     TIMESTAMPTZ,
    created_at     TIMESTAMPTZ DEFAULT NOW()
);
