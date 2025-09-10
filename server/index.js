const express = require('express');
const cors = require('cors');
const path = require('path');
const morgan = require('morgan');
const helmet = require('helmet');
const { v4: uuidv4 } = require('uuid');
const Sentry = require('@sentry/node');
require('dotenv').config();

const connectDB = require('./config/database');

const app = express();

// Sentry init
if (process.env.SENTRY_DSN) {
  Sentry.init({
    dsn: process.env.SENTRY_DSN,
    environment: process.env.NODE_ENV || 'development'
  });
  app.use(Sentry.Handlers.requestHandler());
}

// Connect Database
connectDB();

// Request ID middleware
app.use((req, res, next) => {
  const requestId = req.header('x-request-id') || uuidv4();
  req.requestId = requestId;
  res.setHeader('x-request-id', requestId);
  next();
});

// Logging (access logs)
morgan.token('rid', (req) => req.requestId || '-');
app.use(morgan(':method :url :status :res[content-length] - :response-time ms rid=:rid'));

// Security headers
app.use(helmet());

// Init Middleware
app.use(express.json({ extended: false }));

// CORS configuration
const allowedOrigins = (process.env.CORS_ALLOWED_ORIGINS || '').split(',').map(s => s.trim()).filter(Boolean);
app.use(cors({
  origin: (origin, callback) => {
    if (!origin || allowedOrigins.length === 0 || allowedOrigins.includes(origin)) {
      return callback(null, true);
    }
    return callback(new Error('CORS not allowed'), false);
  },
  credentials: true
}));

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

// Health and readiness endpoints
app.get('/healthz', (req, res) => {
  res.json({ ok: true });
});

app.get('/ready', async (req, res) => {
  const mongoose = require('mongoose');
  try {
    const state = mongoose.connection.readyState;
    const ok = state === 1; // connected
    res.json({ ok, state });
  } catch (e) {
    res.status(500).json({ ok: false, error: e.message });
  }
});

// Serve static assets in production
if (process.env.NODE_ENV === 'production') {
  app.use(express.static(path.join(__dirname, '../client/build')));
  
  app.get('*', (req, res) => {
    res.sendFile(path.resolve(__dirname, '../client', 'build', 'index.html'));
  });
}

const PORT = process.env.PORT || 5000;

// Sentry error handler
if (process.env.SENTRY_DSN) {
  app.use(Sentry.Handlers.errorHandler());
}

app.listen(PORT, () => console.log(`Server started on port ${PORT}`));