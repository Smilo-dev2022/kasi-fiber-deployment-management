const express = require('express');
const cors = require('cors');
const path = require('path');
const { v4: uuidv4 } = require('uuid');

function requestIdMiddleware(req, res, next) {
  req.requestId = req.headers['x-request-id'] || uuidv4();
  res.setHeader('x-request-id', req.requestId);
  next();
}

function buildApp() {
  const app = express();

  // Init Middleware
  app.use(express.json({ extended: false }));

  // CORS allowlist
  const corsAllowlist = (process.env.CORS_ALLOWLIST || '').split(',').map(s => s.trim()).filter(Boolean);
  if (corsAllowlist.length > 0) {
    const corsOptions = {
      origin: function(origin, callback) {
        if (!origin || corsAllowlist.includes(origin)) {
          callback(null, true);
        } else {
          callback(new Error('Not allowed by CORS'));
        }
      },
      credentials: true,
    };
    app.use(cors(corsOptions));
  } else {
    app.use(cors());
  }

  // Request ID for tracing
  app.use(requestIdMiddleware);

  // Basic structured logging
  app.use((req, res, next) => {
    const start = Date.now();
    const { method, url } = req;
    res.on('finish', () => {
      const durationMs = Date.now() - start;
      const logRecord = {
        level: 'info',
        ts: new Date().toISOString(),
        requestId: req.requestId,
        method,
        url,
        status: res.statusCode,
        durationMs,
      };
      // eslint-disable-next-line no-console
      console.log(JSON.stringify(logRecord));
    });
    next();
  });

  // Serve static files (for photo uploads)
  app.use('/uploads', express.static(path.join(__dirname, '../uploads')));

  // Sentry (optional if DSN provided)
  if (process.env.SENTRY_DSN) {
    // Lazy require to avoid dependency if not configured
    const Sentry = require('@sentry/node');
    const { nodeProfilingIntegration } = require('@sentry/profiling-node');
    Sentry.init({
      dsn: process.env.SENTRY_DSN,
      integrations: [nodeProfilingIntegration()],
      environment: process.env.NODE_ENV || 'development',
      tracesSampleRate: 0.1,
    });
    app.use(Sentry.Handlers.requestHandler());
  }

  // Routes
  app.use('/api/auth', require('./routes/auth'));
  app.use('/api/users', require('./routes/users'));
  app.use('/api/pons', require('./routes/pons'));
  app.use('/api/tasks', require('./routes/tasks'));
  app.use('/api/cac', require('./routes/cac'));
  app.use('/api/stringing', require('./routes/stringing'));
  app.use('/api/photos', require('./routes/photos'));
  app.use('/api/smme', require('./routes/smme'));
  app.use('/api/stock', require('./routes/stock'));
  app.use('/api/invoicing', require('./routes/invoicing'));
  app.use('/api/reports', require('./routes/reports'));
  app.use('/api/assets', require('./routes/assets'));
  app.use('/api/settings', require('./routes/settings'));

  // Error handler with structure
  // eslint-disable-next-line no-unused-vars
  app.use((err, req, res, next) => {
    const status = err.status || 500;
    const response = {
      requestId: req.requestId,
      message: err.message || 'Internal Server Error',
    };
    if (process.env.NODE_ENV !== 'production') {
      response.stack = err.stack;
    }
    // eslint-disable-next-line no-console
    console.error(JSON.stringify({
      level: 'error',
      ts: new Date().toISOString(),
      requestId: req.requestId,
      message: err.message,
      stack: err.stack,
    }));
    res.status(status).json(response);
  });

  return app;
}

module.exports = { buildApp };

