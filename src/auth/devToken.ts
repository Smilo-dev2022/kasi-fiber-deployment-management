import jwt from 'jsonwebtoken';

export function issueDevToken(tenantId: string, userId: string) {
  const secret = process.env.JWT_SECRET || 'dev-secret';
  return jwt.sign({ sub: userId, tenant_id: tenantId, role: 'admin' }, secret, { expiresIn: '1d' });
}

