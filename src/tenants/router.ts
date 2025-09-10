import { Router } from 'express';
import type { PoolClient } from 'pg';
import { pool } from '../db.js';
import { z } from 'zod';

export const router = Router();

const ProvisionSchema = z.object({
  name: z.string().min(1),
  code: z.string().min(2).max(32).regex(/^[a-z0-9-]+$/),
  domain: z.string().min(1),
  plan: z.enum(['starter', 'pro', 'enterprise']).default('starter')
});

router.post('/provision', async (req, res) => {
  const parsed = ProvisionSchema.safeParse(req.body);
  if (!parsed.success) return res.status(400).json({ error: parsed.error.flatten() });
  const { name, code, domain, plan } = parsed.data;
  const client: PoolClient = (req as any).pg || (await pool.connect());
  try {
    await client.query('BEGIN');
    const { rows } = await client.query(
      'insert into tenants (name, code, primary_domain, plan) values ($1, $2, $3, $4) returning id',
      [name, code, domain, plan]
    );
    const tenantId = rows[0].id as string;
    await client.query('insert into tenant_domains (tenant_id, domain) values ($1, $2) on conflict do nothing', [tenantId, domain]);
    await client.query('COMMIT');
    res.json({ id: tenantId });
  } catch (err) {
    await client.query('ROLLBACK');
    res.status(500).json({ error: 'Failed to provision tenant' });
  } finally {
    if (!(req as any).pg) client.release?.();
  }
});

