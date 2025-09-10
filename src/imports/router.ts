import { Router } from 'express';
import type { PoolClient } from 'pg';

export const router = Router();

// CSV import stubs (PONs, SMMEs, stock, rate cards, users)
router.post('/csv/:type', async (req, res) => {
  const client: PoolClient = (req as any).pg;
  const tenantId: string | undefined = (req as any).tenantId;
  if (!tenantId) return res.status(401).json({ error: 'Unauthorized' });
  // Parse CSV in client, send JSON rows here; this endpoint upserts accordingly
  res.json({ accepted: true });
});

