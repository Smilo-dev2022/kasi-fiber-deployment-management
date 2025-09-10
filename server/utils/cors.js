function parseAllowlist() {
  const raw = process.env.CORS_ALLOWLIST || '';
  return raw
    .split(',')
    .map(s => s.trim())
    .filter(Boolean);
}

function getCorsOptions() {
  const allowlist = parseAllowlist();
  return {
    origin: function(origin, callback) {
      if (!origin) return callback(null, true);
      if (allowlist.length === 0 || allowlist.includes(origin)) {
        callback(null, true);
      } else {
        callback(new Error('Not allowed by CORS'));
      }
    },
    credentials: true,
    methods: ['GET', 'POST', 'PUT', 'PATCH', 'DELETE', 'OPTIONS'],
    allowedHeaders: ['Content-Type', 'Authorization', 'x-auth-token', 'x-request-id']
  };
}

module.exports = { getCorsOptions };

