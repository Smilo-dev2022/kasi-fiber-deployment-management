import type { PoolClient } from 'pg';

export async function getTenantByHost(client: PoolClient, host: string | undefined) {
  if (!host) return null;
  const domain = host.split(':')[0].toLowerCase();
  const { rows } = await client.query('select t.id, t.code, t.plan from tenant_domains d join tenants t on t.id = d.tenant_id where d.domain = $1', [domain]);
  return rows[0] || null;
}

export async function setPgTenantGuc(client: PoolClient, tenantId: string) {
  await client.query("select set_config('app.current_tenant', $1, true)", [tenantId]);
}

