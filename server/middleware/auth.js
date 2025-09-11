const jwt = require('jsonwebtoken');
const User = require('../models/User');

const auth = async (req, res, next) => {
  const token = req.header('x-auth-token') || req.header('Authorization')?.replace('Bearer ', '');

  if (!token) {
    return res.status(401).json({ message: 'No token, authorization denied' });
  }

  try {
    const primarySecret = process.env.JWT_SECRET || 'fallback_secret';
    const legacySecretRaw = process.env.JWT_SECRET_LEGACY;

    let decoded;
    try {
      decoded = jwt.verify(token, primarySecret);
    } catch (primaryError) {
      if (!legacySecretRaw) throw primaryError;
      // Try legacy secret as-is, then attempt base64-decoded form
      try {
        decoded = jwt.verify(token, legacySecretRaw);
      } catch (legacyError) {
        try {
          const maybeB64 = Buffer.from(legacySecretRaw, 'base64').toString('utf8');
          decoded = jwt.verify(token, maybeB64);
        } catch (legacyB64Error) {
          throw primaryError;
        }
      }
    }
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

module.exports = { auth, authorize };