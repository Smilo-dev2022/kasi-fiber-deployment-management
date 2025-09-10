import 'dotenv/config';
import { Pool } from 'pg';

async function main() {
  const pool = new Pool({ connectionString: process.env.DATABASE_URL });
  const client = await pool.connect();
  try {
    const { rows } = await client.query(
      `insert into usage_daily (tenant_id, day, metric, value)
       select tenant_id, date_trunc('day', created_at)::date as day, metric, sum(quantity)
       from metering_events
       where created_at >= now() - interval '1 day'
       group by tenant_id, date_trunc('day', created_at)::date, metric
       on conflict (tenant_id, day, metric) do update set value = excluded.value
       returning *`
    );
    console.log(`Aggregated: ${rows.length}`);
  } finally {
    client.release();
    await pool.end();
  }
}

main();

