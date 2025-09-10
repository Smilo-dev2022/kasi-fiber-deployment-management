import { Router } from 'express';
import type { PoolClient } from 'pg';
import { loadTheme } from './theme.js';

export const router = Router();

router.get('/', async (req, res) => {
  const client: PoolClient = (req as any).pg;
  const tenantId: string | undefined = (req as any).tenantId;
  if (!tenantId) return res.status(401).json({ error: 'Unauthorized' });
  const theme = await loadTheme(client, tenantId);
  res.json(theme);
});

