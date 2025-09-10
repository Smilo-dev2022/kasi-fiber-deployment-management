const jwt = require('jsonwebtoken');

function getJwtSecrets() {
  const secrets = (process.env.JWT_SECRETS || process.env.JWT_SECRET || '')
    .split(',')
    .map(s => s.trim())
    .filter(Boolean);
  return secrets;
}

function verifyJwt(token) {
  const secrets = getJwtSecrets();
  if (secrets.length === 0) {
    throw new Error('JWT secret not configured');
  }
  let lastError;
  for (const secret of secrets) {
    try {
      return jwt.verify(token, secret);
    } catch (e) {
      lastError = e;
    }
  }
  throw lastError || new Error('Token verification failed');
}

function signJwt(payload, options = { expiresIn: '24h' }) {
  const secrets = getJwtSecrets();
  if (secrets.length === 0) {
    throw new Error('JWT secret not configured');
  }
  return jwt.sign(payload, secrets[0], options);
}

module.exports = { getJwtSecrets, verifyJwt, signJwt };

