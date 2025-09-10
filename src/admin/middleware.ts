import type { Request, Response, NextFunction } from 'express';
import ipaddr from 'ipaddr.js';

export function requireAdminIpFromEnv(req: Request, res: Response, next: NextFunction) {
  const adminCidrs = (process.env.ADMIN_IP_CIDRS || '').split(',').map(s => s.trim()).filter(Boolean);
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

