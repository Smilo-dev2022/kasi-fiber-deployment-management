const express = require('express');
const cors = require('cors');
const path = require('path');
const fs = require('fs');
const pinoHttp = require('pino-http');
const Sentry = require('@sentry/node');
require('dotenv').config();

const connectDB = require('./config/database');
const { requestIdMiddleware } = require('./middleware/requestId');
const { getCorsOptions } = require('./utils/cors');

const app = express();

if (process.env.SENTRY_DSN) {
  Sentry.init({
    dsn: process.env.SENTRY_DSN,
    environment: process.env.NODE_ENV || 'development',
    tracesSampleRate: 0.1
  });
  app.use(Sentry.Handlers.requestHandler());
}

// Connect Database (skip in tests, tests will initialize connection)
if (process.env.NODE_ENV !== 'test') {
  connectDB();
}

// Init Middleware
app.use(express.json({ limit: '12mb' }));
app.use(requestIdMiddleware);
app.use(pinoHttp({
  redact: ['req.headers.authorization', 'req.headers.cookie'],
  customProps: (req) => ({ requestId: req.id, userId: req.user?.id })
}));
app.use(cors(getCorsOptions()));

// Ensure uploads directory exists
try { fs.mkdirSync(path.join(__dirname, '../uploads'), { recursive: true }); } catch (_) {}

// Serve static files (for photo uploads)
app.use('/uploads', express.static(path.join(__dirname, '../uploads')));

// Define Routes
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
app.use('/api/settings', require('./routes/settings'));
app.use('/api/assets', require('./routes/assets'));

// Serve static assets in production
if (process.env.NODE_ENV === 'production') {
  app.use(express.static(path.join(__dirname, '../client/build')));
  
  app.get('*', (req, res) => {
    res.sendFile(path.resolve(__dirname, '../client', 'build', 'index.html'));
  });
}

if (process.env.SENTRY_DSN) {
  app.use(Sentry.Handlers.errorHandler());
}

// Global error handler
// eslint-disable-next-line no-unused-vars
app.use((err, req, res, next) => {
  req.log?.error({ err }, 'Unhandled error');
  res.status(err.status || 500).json({ message: err.message || 'Server error', requestId: req.id });
});

// Start scheduler outside tests
if (process.env.NODE_ENV !== 'test') {
  try {
    require('./jobs/scheduler').start();
  } catch (e) {
    console.warn('Scheduler not started:', e.message);
  }
}

const PORT = process.env.PORT || 5000;

if (process.env.NODE_ENV !== 'test') {
  app.listen(PORT, () => console.log(`Server started on port ${PORT}`));
}

module.exports = app;