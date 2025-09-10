import crypto from 'crypto';

export function verifyPaystackSignature(secret: string, body: string, signatureHeader: string | undefined) {
  if (!signatureHeader) return false;
  const hash = crypto.createHmac('sha512', secret).update(body).digest('hex');
  return hash === signatureHeader;
}

