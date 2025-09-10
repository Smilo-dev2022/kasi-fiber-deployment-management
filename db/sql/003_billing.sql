BEGIN;

ALTER TABLE tenants
  ADD COLUMN IF NOT EXISTS billing_provider text,
  ADD COLUMN IF NOT EXISTS billing_customer_id text;

CREATE INDEX IF NOT EXISTS idx_tenants_billing ON tenants(billing_provider, billing_customer_id);

COMMIT;

