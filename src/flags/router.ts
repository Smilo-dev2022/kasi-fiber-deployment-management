import { Router } from 'express';
import type { PoolClient } from 'pg';

export const router = Router();

router.get('/', async (req, res) => {
  const client: PoolClient = (req as any).pg;
  const tenantId: string | undefined = (req as any).tenantId;
  if (!tenantId) return res.status(401).json({ error: 'Unauthorized' });
  const { rows } = await client.query('select flag_key, value from feature_flags');
  res.json(rows.reduce((acc: Record<string, any>, r: any) => { acc[r.flag_key] = r.value; return acc; }, {}));
});

router.post('/', async (req, res) => {
  const client: PoolClient = (req as any).pg;
  const tenantId: string | undefined = (req as any).tenantId;
  if (!tenantId) return res.status(401).json({ error: 'Unauthorized' });
  const flags = req.body || {};
  const keys = Object.keys(flags);
  if (keys.length === 0) return res.json({});
  for (const key of keys) {
    await client.query(
      'insert into feature_flags (tenant_id, flag_key, value) values ($1, $2, $3) on conflict (tenant_id, flag_key) do update set value = excluded.value, updated_at = now()',
      [tenantId, key, flags[key]]
    );
  }
  res.json({ ok: true });
});

