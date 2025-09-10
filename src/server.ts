import 'dotenv/config';
import express from 'express';
import cors from 'cors';
import helmet from 'helmet';
import pino from 'pino';
import pinoHttp from 'pino-http';
import { PoolClient } from 'pg';
import { pool } from './db.js';
import jwt from 'jsonwebtoken';
import { z } from 'zod';
import ipaddr from 'ipaddr.js';
import { createRateLimiter } from './util/rateLimit.js';
import { getTenantByHost, setPgTenantGuc } from './util/tenancy.js';
import { audit } from './util/audit.js';
import { router as uploadsRouter } from './uploads/router.js';
import { router as billingRouter } from './billing/router.js';
import { router as provisioningRouter } from './tenants/router.js';
import { router as flagsRouter } from './flags/router.js';
import { meteringMiddleware } from './util/metering.js';
import { v4 as uuidv4 } from 'uuid';
import { router as themeRouter } from './theme/router.js';
import { router as importsRouter } from './imports/router.js';

const logger = pino({ level: process.env.NODE_ENV === 'production' ? 'info' : 'debug' });

const app = express();
app.use(helmet());
app.use(cors());
app.use(express.json({ limit: '2mb' }));
app.use(pinoHttp({
  genReqId: (req) => (req.headers['x-request-id'] as string) || uuidv4(),
  customProps: (req) => ({ tenantId: (req as any).tenantId || null })
}));

const jwtSecret = process.env.JWT_SECRET || 'dev-secret';
const adminCidrs = (process.env.ADMIN_IP_CIDRS || '').split(',').map(s => s.trim()).filter(Boolean);

// Simple IP allow list middleware for admin routes
function requireAdminIp(req: express.Request, res: express.Response, next: express.NextFunction) {
  if (adminCidrs.length === 0) return next();
  const remote = (req.headers['x-forwarded-for'] as string)?.split(',')[0]?.trim() || req.socket.remoteAddress || '';
  try {
    const ip = ipaddr.parse(remote).toNormalizedString();
    const allowed = adminCidrs.some(cidr => ipaddr.parse(ip).match(ipaddr.parseCIDR(cidr as string)));
    if (!allowed) return res.status(403).json({ error: 'Forbidden' });
    return next();
  } catch {
    return res.status(403).json({ error: 'Forbidden' });
  }
}

// Auth schema
const JwtPayloadSchema = z.object({ sub: z.string(), tenant_id: z.string().uuid(), role: z.string().optional() });

// Per-request context binder: resolve tenant by Host or JWT; start TX; set PG GUC; release on finish
app.use(async (req, res, next) => {
  const host = (req.headers['x-forwarded-host'] as string) || req.headers.host || '';
  const client = await pool.connect();
  (req as any).pg = client;
  let finished = false;
  const safeFinish = async (commit: boolean) => {
    if (finished) return; finished = true;
    try { await client.query(commit ? 'COMMIT' : 'ROLLBACK'); } catch {}
    client.release();
  };
  res.on('finish', () => { void safeFinish(true); });
  res.on('close', () => { void safeFinish(false); });
  try {
    await client.query('BEGIN');
    const tenant = await getTenantByHost(client, host);
    let jwtTenantId: string | undefined;
    const auth = req.headers.authorization;
    if (auth?.startsWith('Bearer ')) {
      try {
        const decoded = jwt.verify(auth.slice(7), jwtSecret);
        const parsed = JwtPayloadSchema.safeParse(decoded);
        if (parsed.success) jwtTenantId = parsed.data.tenant_id;
      } catch (_) {}
    }
    // If both host mapping and JWT exist, enforce they match
    if (tenant?.id && jwtTenantId && tenant.id !== jwtTenantId) {
      return res.status(401).json({ error: 'Tenant mismatch' });
    }
    const tenantId = tenant?.id || jwtTenantId;
    if (tenantId) {
      await setPgTenantGuc(client, tenantId);
      (req as any).tenantId = tenantId;
    }
    return next();
  } catch (err) {
    req.log?.error({ err }, 'tenant context error');
    return res.status(500).json({ error: 'Internal error' });
  }
});

// Rate limits per tenant (basic)
const rateLimiter = createRateLimiter();
app.use(async (req, res, next) => {
  try {
    const tenantId = (req as any).tenantId || 'public';
    await rateLimiter.consume(`${tenantId}:${req.ip}`);
    next();
  } catch {
    res.status(429).json({ error: 'Too many requests' });
  }
});

// Metering: count API calls per tenant (exclude health and webhooks)
app.use(meteringMiddleware);

// Health/ready/billing status
app.get('/health', (req, res) => res.json({ ok: true }));
app.get('/ready', async (req, res) => {
  try {
    await pool.query('select 1');
    res.json({ ready: true });
  } catch {
    res.status(500).json({ ready: false });
  }
});
app.get('/billing/status', (req, res) => res.json({ billing: 'ok' }));

// Admin-only example route (IP allowlist)
app.get('/admin/tenants', requireAdminIp, async (req, res) => {
  const client: PoolClient = (req as any).pg || (await pool.connect());
  try {
    const { rows } = await client.query('select id, code, name, plan, status from tenants order by created_at desc');
    res.json(rows);
  } finally {
    if (!(req as any).pg) client.release();
  }
});

// Mount routers
app.use('/uploads', uploadsRouter);
app.use('/billing', billingRouter);
app.use('/tenants', provisioningRouter);
app.use('/flags', flagsRouter);
app.use('/theme', themeRouter);
app.use('/imports', importsRouter);

// Example themed email/PDF fetch
app.get('/theme', async (req, res) => {
  const client: PoolClient = (req as any).pg || (await pool.connect());
  try {
    const tenantId: string | undefined = (req as any).tenantId;
    if (!tenantId) return res.status(401).json({ error: 'Unauthorized' });
    const { rows } = await client.query('select theme from tenants where id = $1', [tenantId]);
    res.json(rows[0]?.theme || {});
  } finally {
    if (!(req as any).pg) client.release();
  }
});

// Audit log example
app.post('/_audit_example', async (req, res) => {
  const client: PoolClient = (req as any).pg || (await pool.connect());
  try {
    const tenantId: string | undefined = (req as any).tenantId;
    if (!tenantId) return res.status(401).json({ error: 'Unauthorized' });
    await audit(client, tenantId, {
      actorUserId: null,
      action: 'example_event',
      entity: 'example',
      entityId: '1',
      metadata: { note: 'hello' },
      ip: req.ip
    });
    res.json({ ok: true });
  } finally {
    if (!(req as any).pg) client.release();
  }
});

const port = Number(process.env.PORT || 3000);
app.listen(port, () => {
  logger.info({ port }, 'server started');
});

