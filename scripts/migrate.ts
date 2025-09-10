import 'dotenv/config';
import { readFileSync, readdirSync } from 'fs';
import { join } from 'path';
import { Pool } from 'pg';

async function main() {
  const pool = new Pool({ connectionString: process.env.DATABASE_URL });
  const client = await pool.connect();
  try {
    const dir = join(process.cwd(), 'db/sql');
    const files = readdirSync(dir).filter(f => f.endsWith('.sql')).sort();
    for (const f of files) {
      const sql = readFileSync(join(dir, f), 'utf8');
      console.log('Running', f);
      await client.query('BEGIN');
      await client.query(sql);
      await client.query('COMMIT');
    }
    console.log('Migrations complete');
  } catch (err) {
    console.error('Migration failed:', err);
    process.exit(1);
  } finally {
    client.release();
    await pool.end();
  }
}

main();

