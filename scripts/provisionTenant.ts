import 'dotenv/config';
import { Pool } from 'pg';

const args = Object.fromEntries(process.argv.slice(2).reduce((acc: [string, string][], arg) => {
  const [k, v] = arg.startsWith('--') ? arg.slice(2).split('=') : arg.split('=');
  if (k) acc.push([k, v ?? 'true']);
  return acc;
}, []));

async function main() {
  const pool = new Pool({ connectionString: process.env.DATABASE_URL });
  const name = args.name || args.n;
  const code = args.code || args.c;
  const domain = args.domain || args.d;
  const plan = args.plan || 'starter';
  const billingProvider = args.billingProvider || args.billing_provider || '';
  const billingCustomerId = args.billingCustomerId || args.billing_customer_id || '';
  if (!name || !code || !domain) {
    console.error('Usage: npm run provision -- --name "Acme" --code acme --domain app.acme.co --plan starter');
    process.exit(1);
  }
  const client = await pool.connect();
  try {
    await client.query('BEGIN');
    const { rows } = await client.query(
      'insert into tenants (name, code, primary_domain, plan) values ($1, $2, $3, $4) returning id',
      [name, code, domain, plan]
    );
    const tenantId = rows[0].id as string;
    await client.query('insert into tenant_domains (tenant_id, domain) values ($1, $2) on conflict do nothing', [tenantId, domain]);
    if (billingProvider && billingCustomerId) {
      await client.query('update tenants set billing_provider = $1, billing_customer_id = $2 where id = $3', [billingProvider, billingCustomerId, tenantId]);
    }
    await client.query('COMMIT');
    console.log(JSON.stringify({ id: tenantId, code, domain }, null, 2));
  } catch (err) {
    await client.query('ROLLBACK');
    console.error('Provision failed:', err);
    process.exit(1);
  } finally {
    client.release();
    await pool.end();
  }
}

main();

