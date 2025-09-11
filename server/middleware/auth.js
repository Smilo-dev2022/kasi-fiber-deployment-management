const jwt = require('jsonwebtoken');
const crypto = require('crypto');
const User = require('../models/User');

const auth = async (req, res, next) => {
  const token = req.header('x-auth-token') || req.header('Authorization')?.replace('Bearer ', '');

  if (!token) {
    return res.status(401).json({ message: 'No token, authorization denied' });
  }

  try {
    const decoded = jwt.verify(token, process.env.JWT_SECRET || 'fallback_secret');
    const user = await User.findById(decoded.user.id).select('-password');
    
    if (!user || !user.isActive) {
      return res.status(401).json({ message: 'Token is not valid' });
    }

    req.user = user;
    next();
  } catch (error) {
    res.status(401).json({ message: 'Token is not valid' });
  }
};

// Role-based authorization
const authorize = (...roles) => {
  return (req, res, next) => {
    if (!req.user) {
      return res.status(401).json({ message: 'Access denied' });
    }

    if (!roles.includes(req.user.role)) {
      return res.status(403).json({ message: 'Insufficient permissions' });
    }

    next();
  };
};

// HMAC + IP allowlist for webhooks
const webhookGuard = (envPrefix) => {
  const allow = (process.env[`${envPrefix}_ALLOW_IPS`] || '').split(',').map(s => s.trim()).filter(Boolean);
  const secret = process.env[`${envPrefix}_HMAC_SECRET`];
  return (req, res, next) => {
    if (allow.length) {
      const ip = req.ip || (req.connection && req.connection.remoteAddress);
      if (!allow.includes(ip)) {
        return res.status(403).json({ message: 'IP not allowed' });
      }
    }
    if (secret) {
      const sig = req.header('X-Signature') || req.header('X-Hub-Signature');
      if (!sig) {
        return res.status(401).json({ message: 'Missing signature' });
      }
      const h = crypto.createHmac('sha256', secret).update(req.rawBody || JSON.stringify(req.body || {})).digest('hex');
      if (!crypto.timingSafeEqual(Buffer.from(sig), Buffer.from(h))) {
        return res.status(401).json({ message: 'Invalid signature' });
      }
    }
    next();
  };
};

module.exports = { auth, authorize, webhookGuard };