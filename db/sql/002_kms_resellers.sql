BEGIN;

-- Optional per-tenant KMS key references (app side manages KMS)
CREATE TABLE IF NOT EXISTS tenant_kms_keys (
  tenant_id uuid PRIMARY KEY REFERENCES tenants(id) ON DELETE CASCADE,
  kms_key_arn text NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now()
);

-- Reseller channel
CREATE TABLE IF NOT EXISTS resellers (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  name text NOT NULL,
  tier text NOT NULL,
  margin_percent int NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS reseller_tenants (
  reseller_id uuid NOT NULL REFERENCES resellers(id) ON DELETE CASCADE,
  tenant_id uuid NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
  created_at timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (reseller_id, tenant_id)
);

COMMIT;

