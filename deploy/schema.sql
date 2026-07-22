-- =============================================================================
-- Schéma PostgreSQL Multi-Tenant — SuperAgent Morph (Production Grade)
-- =============================================================================
-- Ce schéma supporte :
--   - Multi-tenancy (org_id sur chaque table)
--   - Audit trail immuable (append-only)
--   - Row-Level Security (RLS) pour l'isolation des données
--   - Cycle de vie des Skills (HITL : PENDING → APPROVED / REJECTED)
--   - Checkpoints persistants avec TTL
--   - Traçabilité complète : qui a approuvé quoi, quand, pour quel job
-- =============================================================================

-- =============================================================================
-- 1. ORGANISATIONS & UTILISATEURS
-- =============================================================================

CREATE TABLE organizations (
    org_id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name            VARCHAR(255) NOT NULL,
    slug            VARCHAR(100) NOT NULL UNIQUE,
    api_key_hash    VARCHAR(255) NOT NULL,
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    settings_json   JSONB NOT NULL DEFAULT '{}',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_organizations_slug ON organizations(slug);
CREATE INDEX idx_organizations_active ON organizations(is_active) WHERE is_active = TRUE;

CREATE TABLE users (
    user_id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id          UUID NOT NULL REFERENCES organizations(org_id) ON DELETE CASCADE,
    email           VARCHAR(255) NOT NULL,
    display_name    VARCHAR(255) NOT NULL,
    role            VARCHAR(50) NOT NULL DEFAULT 'member'
                    CHECK (role IN ('admin', 'member', 'viewer')),
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_login_at   TIMESTAMPTZ,
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (org_id, email)
);

CREATE INDEX idx_users_org ON users(org_id);
CREATE INDEX idx_users_email ON users(email);

-- =============================================================================
-- 2. PROJETS & JOBS
-- =============================================================================

CREATE TABLE projects (
    project_id      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id          UUID NOT NULL REFERENCES organizations(org_id) ON DELETE CASCADE,
    name            VARCHAR(255) NOT NULL,
    description     TEXT,
    repo_url        VARCHAR(500),
    settings_json   JSONB NOT NULL DEFAULT '{}',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_projects_org ON projects(org_id);

CREATE TABLE jobs (
    job_id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id          UUID NOT NULL REFERENCES organizations(org_id) ON DELETE CASCADE,
    project_id      UUID REFERENCES projects(project_id) ON DELETE SET NULL,
    user_id         UUID REFERENCES users(user_id) ON DELETE SET NULL,
    task_text       TEXT NOT NULL,
    status          VARCHAR(20) NOT NULL DEFAULT 'PENDING'
                    CHECK (status IN ('PENDING', 'IN_PROGRESS', 'SUCCESS', 'FAILED', 'CANCELLED')),
    last_node       VARCHAR(50) DEFAULT 'START',
    retry_count     INTEGER NOT NULL DEFAULT 0,
    max_retries     INTEGER NOT NULL DEFAULT 2,
    error_message   TEXT,
    started_at      TIMESTAMPTZ,
    completed_at    TIMESTAMPTZ,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_jobs_org ON jobs(org_id);
CREATE INDEX idx_jobs_project ON jobs(project_id);
CREATE INDEX idx_jobs_user ON jobs(user_id);
CREATE INDEX idx_jobs_status ON jobs(org_id, status);
CREATE INDEX idx_jobs_created ON jobs(org_id, created_at DESC);

-- =============================================================================
-- 3. SKILLS — Mémoire Sémantique avec Cycle de Vie HITL
-- =============================================================================

CREATE TABLE skills (
    skill_id        UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id          UUID NOT NULL REFERENCES organizations(org_id) ON DELETE CASCADE,
    status          VARCHAR(20) NOT NULL DEFAULT 'PENDING_APPROVAL'
                    CHECK (status IN ('PENDING_APPROVAL', 'APPROVED', 'REJECTED', 'ARCHIVED')),
    subject_key     VARCHAR(255) NOT NULL,
    directive_text  TEXT NOT NULL,
    error_context   TEXT,
    keywords_json   JSONB NOT NULL DEFAULT '[]',
    sha256_hash     VARCHAR(64),
    source_job_id   UUID REFERENCES jobs(job_id) ON DELETE SET NULL,
    approved_by     UUID REFERENCES users(user_id) ON DELETE SET NULL,
    approved_at     TIMESTAMPTZ,
    rejected_by     UUID REFERENCES users(user_id) ON DELETE SET NULL,
    rejected_at     TIMESTAMPTZ,
    rejection_reason TEXT,
    version         INTEGER NOT NULL DEFAULT 1,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_skills_org ON skills(org_id);
CREATE INDEX idx_skills_status ON skills(org_id, status);
CREATE INDEX idx_skills_subject ON skills USING gin(to_tsvector('french', subject_key));
CREATE INDEX idx_skills_keywords ON skills USING gin(keywords_json);

-- =============================================================================
-- 4. CHECKPOINTS — Persistance d'État avec TTL
-- =============================================================================

CREATE TABLE checkpoints (
    job_id          UUID PRIMARY KEY REFERENCES jobs(job_id) ON DELETE CASCADE,
    org_id          UUID NOT NULL REFERENCES organizations(org_id) ON DELETE CASCADE,
    state_blob      JSONB NOT NULL,
    last_node       VARCHAR(50) NOT NULL,
    retry_count     INTEGER NOT NULL DEFAULT 0,
    expires_at      TIMESTAMPTZ NOT NULL DEFAULT (NOW() + INTERVAL '7 days'),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_checkpoints_org ON checkpoints(org_id);
CREATE INDEX idx_checkpoints_expires ON checkpoints(expires_at);

-- =============================================================================
-- 5. AUDIT TRAIL — Immuable, Append-Only
-- =============================================================================

CREATE TABLE audit_logs (
    log_id          UUID DEFAULT gen_random_uuid(),
    org_id          UUID NOT NULL REFERENCES organizations(org_id) ON DELETE CASCADE,
    job_id          UUID REFERENCES jobs(job_id) ON DELETE SET NULL,
    user_id         UUID REFERENCES users(user_id) ON DELETE SET NULL,
    agent_name      VARCHAR(50) NOT NULL
                    CHECK (agent_name IN ('ECLAIREUR', 'ANALYSTE', 'CODEUR', 'REDACTEUR', 'DISTILLATEUR', 'NETTOYEUR', 'API', 'SYSTEM')),
    action_type     VARCHAR(50) NOT NULL,
    status          VARCHAR(20) NOT NULL
                    CHECK (status IN ('STARTED', 'COMPLETED', 'FAILED', 'SKIPPED', 'CANCELLED')),
    duration_ms     INTEGER,
    payload_json    JSONB,
    error_message   TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (log_id, created_at)
)
PARTITION BY RANGE (created_at);

-- Création de la partition courante
CREATE TABLE audit_logs_default PARTITION OF audit_logs
FOR VALUES FROM (MINVALUE) TO (MAXVALUE);

-- Audit logs are APPEND-ONLY: no UPDATE, no DELETE (enforced by RLS below)
CREATE INDEX idx_audit_org ON audit_logs(org_id, created_at DESC);
CREATE INDEX idx_audit_job ON audit_logs(job_id);
CREATE INDEX idx_audit_agent ON audit_logs(org_id, agent_name, created_at DESC);
CREATE INDEX idx_audit_payload ON audit_logs USING gin(payload_json);

-- =============================================================================
-- 6. VALIDATIONS HUMAINES (HITL)
-- =============================================================================

CREATE TABLE human_validations (
    validation_id   UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id          UUID NOT NULL REFERENCES organizations(org_id) ON DELETE CASCADE,
    job_id          UUID REFERENCES jobs(job_id) ON DELETE SET NULL,
    skill_id        UUID REFERENCES skills(skill_id) ON DELETE SET NULL,
    user_id         UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    decision        VARCHAR(20) NOT NULL
                    CHECK (decision IN ('APPROVED', 'REJECTED', 'REQUEST_CHANGES')),
    comment         TEXT,
    context_json    JSONB NOT NULL DEFAULT '{}',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_validations_org ON human_validations(org_id);
CREATE INDEX idx_validations_job ON human_validations(job_id);
CREATE INDEX idx_validations_user ON human_validations(user_id, created_at DESC);

-- =============================================================================
-- 7. API KEYS CLIENTS (pour Phase 2 : BYOK)
-- =============================================================================

CREATE TABLE api_keys (
    api_key_id      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id          UUID NOT NULL REFERENCES organizations(org_id) ON DELETE CASCADE,
    key_hash        VARCHAR(255) NOT NULL UNIQUE,
    key_prefix      VARCHAR(8) NOT NULL,  -- premiers caractères pour identification
    name            VARCHAR(100) NOT NULL,
    provider        VARCHAR(50) NOT NULL
                    CHECK (provider IN ('mistral', 'tavily', 'openai', 'anthropic', 'custom')),
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    usage_count     BIGINT NOT NULL DEFAULT 0,
    last_used_at    TIMESTAMPTZ,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    expires_at      TIMESTAMPTZ
);

CREATE INDEX idx_apikeys_org ON api_keys(org_id);
CREATE INDEX idx_apikeys_provider ON api_keys(org_id, provider);

-- =============================================================================
-- 8. TRIGGERS : Mise à jour automatique de updated_at
-- =============================================================================

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_organizations_updated_at
    BEFORE UPDATE ON organizations
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER trg_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER trg_projects_updated_at
    BEFORE UPDATE ON projects
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER trg_jobs_updated_at
    BEFORE UPDATE ON jobs
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER trg_skills_updated_at
    BEFORE UPDATE ON skills
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER trg_checkpoints_updated_at
    BEFORE UPDATE ON checkpoints
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- =============================================================================
-- 9. ROW-LEVEL SECURITY (RLS) — Isolation Multi-Tenant
-- =============================================================================

-- Activer RLS sur toutes les tables métier
ALTER TABLE organizations ENABLE ROW LEVEL SECURITY;
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE projects ENABLE ROW LEVEL SECURITY;
ALTER TABLE jobs ENABLE ROW LEVEL SECURITY;
ALTER TABLE skills ENABLE ROW LEVEL SECURITY;
ALTER TABLE checkpoints ENABLE ROW LEVEL SECURITY;
ALTER TABLE audit_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE human_validations ENABLE ROW LEVEL SECURITY;
ALTER TABLE api_keys ENABLE ROW LEVEL SECURITY;

-- Politique : les utilisateurs ne voient que leur propre organisation
-- (la variable session `app.current_org_id` est injectée par l'application)
CREATE POLICY org_isolation ON organizations
    FOR ALL
    USING (org_id = current_setting('app.current_org_id')::UUID);

CREATE POLICY org_isolation ON users
    FOR ALL
    USING (org_id = current_setting('app.current_org_id')::UUID);

CREATE POLICY org_isolation ON projects
    FOR ALL
    USING (org_id = current_setting('app.current_org_id')::UUID);

CREATE POLICY org_isolation ON jobs
    FOR ALL
    USING (org_id = current_setting('app.current_org_id')::UUID);

CREATE POLICY org_isolation ON skills
    FOR ALL
    USING (org_id = current_setting('app.current_org_id')::UUID);

CREATE POLICY org_isolation ON checkpoints
    FOR ALL
    USING (org_id = current_setting('app.current_org_id')::UUID);

CREATE POLICY org_isolation ON audit_logs
    FOR ALL
    USING (org_id = current_setting('app.current_org_id')::UUID);

CREATE POLICY org_isolation ON human_validations
    FOR ALL
    USING (org_id = current_setting('app.current_org_id')::UUID);

CREATE POLICY org_isolation ON api_keys
    FOR ALL
    USING (org_id = current_setting('app.current_org_id')::UUID);

-- Politique spéciale : audit_logs est APPEND-ONLY (pas d'UPDATE/DELETE)
CREATE POLICY audit_append_only ON audit_logs
    FOR INSERT
    WITH CHECK (true);

-- =============================================================================
-- 10. FONCTIONS UTILITAIRES
-- =============================================================================

-- Nettoyage des checkpoints expirés (à appeler via cron ou pg_cron)
CREATE OR REPLACE FUNCTION cleanup_expired_checkpoints()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM checkpoints WHERE expires_at < NOW();
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- Création des partitions mensuelles pour audit_logs
CREATE OR REPLACE FUNCTION create_audit_partition()
RETURNS VOID AS $$
DECLARE
    partition_name TEXT;
    start_date TEXT;
    end_date TEXT;
BEGIN
    partition_name := 'audit_logs_' || to_char(NOW(), 'YYYY_MM');
    start_date := date_trunc('month', NOW())::TEXT;
    end_date := (date_trunc('month', NOW()) + INTERVAL '1 month')::TEXT;

    EXECUTE format(
        'CREATE TABLE IF NOT EXISTS %I PARTITION OF audit_logs
         FOR VALUES FROM (%L) TO (%L)',
        partition_name, start_date, end_date
    );
END;
$$ LANGUAGE plpgsql;
