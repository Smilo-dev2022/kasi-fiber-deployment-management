import type { Request, Response, NextFunction } from 'express';
import type { PoolClient } from 'pg';

export async function recordApiCall(client: PoolClient, tenantId: string | undefined) {
  if (!tenantId) return;
  await client.query(
    'insert into metering_events (tenant_id, metric, subject_id, quantity) values ($1, $2, $3, $4)',
    [tenantId, 'api_calls', null, 1]
  );
}

export function meteringMiddleware(req: Request, res: Response, next: NextFunction) {
  // Skip health and stripe webhooks
  if (req.path === '/health' || req.path === '/ready' || req.path.startsWith('/billing/stripe/webhook')) {
    return next();
  }
  const client: PoolClient = (req as any).pg;
  const tenantId: string | undefined = (req as any).tenantId;
  recordApiCall(client, tenantId).finally(() => next());
}

