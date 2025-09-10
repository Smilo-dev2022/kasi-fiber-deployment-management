-- Initial schema with multi-tenant RLS by tenant_id
-- Run with: psql $DATABASE_URL -v ON_ERROR_STOP=1 -f db/sql/001_init.sql

BEGIN;

CREATE EXTENSION IF NOT EXISTS pgcrypto; -- for gen_random_uuid

-- Optional enums
DO $$ BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'plan_type') THEN
    CREATE TYPE plan_type AS ENUM ('starter', 'pro', 'enterprise');
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'tenant_status') THEN
    CREATE TYPE tenant_status AS ENUM ('active', 'trial', 'suspended', 'deleted');
  END IF;
END $$;

-- Helper function to read current tenant from GUC
CREATE OR REPLACE FUNCTION current_tenant_uuid() RETURNS uuid LANGUAGE sql STABLE AS $$
  SELECT NULLIF(current_setting('app.current_tenant', true), '')::uuid;
$$;

-- Tenants
CREATE TABLE IF NOT EXISTS tenants (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  code text NOT NULL UNIQUE,
  name text NOT NULL,
  primary_domain text UNIQUE,
  plan plan_type NOT NULL DEFAULT 'starter',
  flags jsonb NOT NULL DEFAULT '{}',
  theme jsonb NOT NULL DEFAULT jsonb_build_object(
    'primaryColor', '#0ea5e9',
    'secondaryColor', '#111827',
    'logoUrl', NULL,
    'faviconUrl', NULL,
    'emailSenderName', NULL,
    'emailSenderId', NULL
  ),
  status tenant_status NOT NULL DEFAULT 'active',
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS tenant_domains (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id uuid NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
  domain text NOT NULL UNIQUE,
  created_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_tenant_domains_tenant ON tenant_domains(tenant_id);

-- Users (example)
CREATE TABLE IF NOT EXISTS users (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id uuid NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
  email text NOT NULL,
  password_hash text,
  role text NOT NULL DEFAULT 'user',
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE(tenant_id, email)
);
CREATE INDEX IF NOT EXISTS idx_users_tenant ON users(tenant_id);

-- Feature flags per tenant
CREATE TABLE IF NOT EXISTS feature_flags (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id uuid NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
  flag_key text NOT NULL,
  value jsonb NOT NULL,
  updated_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE(tenant_id, flag_key)
);
CREATE INDEX IF NOT EXISTS idx_feature_flags_tenant ON feature_flags(tenant_id);

-- Theme table (optional override beyond tenants.theme JSON)
CREATE TABLE IF NOT EXISTS themes (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id uuid NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
  primary_color text,
  secondary_color text,
  logo_url text,
  favicon_url text,
  email_sender_name text,
  email_sender_id text,
  pdf_footer text,
  updated_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE(tenant_id)
);

-- Files metadata (S3 key references)
CREATE TABLE IF NOT EXISTS files (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id uuid NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
  s3_key text NOT NULL,
  content_type text,
  size_bytes bigint,
  created_by uuid,
  created_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_files_tenant ON files(tenant_id);

-- Audit logs
CREATE TABLE IF NOT EXISTS audit_logs (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id uuid NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
  actor_user_id uuid,
  action text NOT NULL,
  entity text,
  entity_id text,
  metadata jsonb NOT NULL DEFAULT '{}',
  ip inet,
  created_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_audit_logs_tenant ON audit_logs(tenant_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_entity ON audit_logs(tenant_id, entity, entity_id);

-- Metering
DO $$ BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'metric_type') THEN
    CREATE TYPE metric_type AS ENUM ('pon_active', 'photos_gb', 'users', 'api_calls');
  END IF;
END $$;

CREATE TABLE IF NOT EXISTS metering_events (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id uuid NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
  metric metric_type NOT NULL,
  subject_id text,
  quantity numeric NOT NULL DEFAULT 1,
  metadata jsonb NOT NULL DEFAULT '{}',
  created_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_metering_events_tenant_metric ON metering_events(tenant_id, metric, created_at);

CREATE TABLE IF NOT EXISTS usage_daily (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id uuid NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
  day date NOT NULL,
  metric metric_type NOT NULL,
  value numeric NOT NULL,
  UNIQUE(tenant_id, day, metric)
);
CREATE INDEX IF NOT EXISTS idx_usage_daily_tenant_day ON usage_daily(tenant_id, day);

-- Plan limits (for enforcement)
CREATE TABLE IF NOT EXISTS plan_limits (
  plan plan_type PRIMARY KEY,
  limits jsonb NOT NULL
);
INSERT INTO plan_limits(plan, limits) VALUES
  ('starter', '{"pon_max":20,"users_max":10,"reports":false,"sla":false}')
  ON CONFLICT (plan) DO NOTHING;
INSERT INTO plan_limits(plan, limits) VALUES
  ('pro', '{"pon_max":null,"users_max":null,"reports":true,"sla":true}')
  ON CONFLICT (plan) DO NOTHING;
INSERT INTO plan_limits(plan, limits) VALUES
  ('enterprise', '{"pon_max":null,"users_max":null,"reports":true,"sla":true,"sso":true,"private_cloud":true}')
  ON CONFLICT (plan) DO NOTHING;

-- Admin IP allowlist (global)
CREATE TABLE IF NOT EXISTS admin_ip_allowlist (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  cidr text NOT NULL UNIQUE,
  description text,
  created_at timestamptz NOT NULL DEFAULT now()
);

-- Timestamps trigger
CREATE OR REPLACE FUNCTION set_updated_at() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  NEW.updated_at = now();
  RETURN NEW;
END $$;

DO $$ BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'users_set_updated_at') THEN
    CREATE TRIGGER users_set_updated_at BEFORE UPDATE ON users FOR EACH ROW EXECUTE FUNCTION set_updated_at();
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'themes_set_updated_at') THEN
    CREATE TRIGGER themes_set_updated_at BEFORE UPDATE ON themes FOR EACH ROW EXECUTE FUNCTION set_updated_at();
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'tenants_set_updated_at') THEN
    CREATE TRIGGER tenants_set_updated_at BEFORE UPDATE ON tenants FOR EACH ROW EXECUTE FUNCTION set_updated_at();
  END IF;
END $$;

-- Enable Row Level Security and policies by tenant_id where applicable
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE feature_flags ENABLE ROW LEVEL SECURITY;
ALTER TABLE themes ENABLE ROW LEVEL SECURITY;
ALTER TABLE files ENABLE ROW LEVEL SECURITY;
ALTER TABLE audit_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE metering_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE usage_daily ENABLE ROW LEVEL SECURITY;

-- Tenants and tenant_domains are managed by platform admins; no RLS for tenants to avoid self-lockout in bootstrap.

-- Generic RLS: tenant_id must match current_tenant_uuid()
CREATE POLICY rls_users_tenant ON users USING (tenant_id = current_tenant_uuid()) WITH CHECK (tenant_id = current_tenant_uuid());
CREATE POLICY rls_feature_flags_tenant ON feature_flags USING (tenant_id = current_tenant_uuid()) WITH CHECK (tenant_id = current_tenant_uuid());
CREATE POLICY rls_themes_tenant ON themes USING (tenant_id = current_tenant_uuid()) WITH CHECK (tenant_id = current_tenant_uuid());
CREATE POLICY rls_files_tenant ON files USING (tenant_id = current_tenant_uuid()) WITH CHECK (tenant_id = current_tenant_uuid());
CREATE POLICY rls_audit_tenant ON audit_logs USING (tenant_id = current_tenant_uuid()) WITH CHECK (tenant_id = current_tenant_uuid());
CREATE POLICY rls_metering_tenant ON metering_events USING (tenant_id = current_tenant_uuid()) WITH CHECK (tenant_id = current_tenant_uuid());
CREATE POLICY rls_usage_daily_tenant ON usage_daily USING (tenant_id = current_tenant_uuid()) WITH CHECK (tenant_id = current_tenant_uuid());

COMMIT;

