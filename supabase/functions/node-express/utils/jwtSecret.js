function isTruthy(value) {
  if (!value) return false;
  const normalized = String(value).trim().toLowerCase();
  return normalized === '1' || normalized === 'true' || normalized === 'yes' || normalized === 'y';
}

function looksLikeBase64(value) {
  if (!value) return false;
  const base64Regex = /^[A-Za-z0-9+/]+={0,2}$/;
  return value.length % 4 === 0 && base64Regex.test(value);
}

function getJwtSecret() {
  const rawSecret = process.env.JWT_SECRET;
  if (!rawSecret) {
    throw new Error('Server not configured: JWT_SECRET is missing');
  }

  const encoding = (process.env.JWT_SECRET_ENCODING || '').trim().toLowerCase();
  const isBase64Flag = isTruthy(process.env.JWT_SECRET_BASE64);

  const shouldDecodeBase64 = isBase64Flag || encoding === 'base64' || looksLikeBase64(rawSecret);

  if (shouldDecodeBase64) {
    try {
      return Buffer.from(rawSecret, 'base64');
    } catch (err) {
      throw new Error('Invalid base64 JWT secret provided');
    }
  }

  return Buffer.from(rawSecret, 'utf8');
}

module.exports = { getJwtSecret };

