const express = require('express');
const cors = require('cors');
const path = require('path');
const fs = require('fs');
const morgan = require('morgan');
const helmet = require('helmet');
const rateLimit = require('express-rate-limit');
const { v4: uuidv4 } = require('uuid');
const mongoose = require('mongoose');
const Sentry = require('@sentry/node');
require('dotenv').config();

const connectDB = require('./config/database');

const app = express();

// Sentry setup (optional)
if (process.env.SENTRY_DSN) {
  Sentry.init({
    dsn: process.env.SENTRY_DSN,
    tracesSampleRate: Number(process.env.SENTRY_TRACES_SAMPLE_RATE || 0.0)
  });
  app.use(Sentry.Handlers.requestHandler());
}

// Connect Database
connectDB();

// Ensure uploads folder exists
const uploadsDir = path.join(__dirname, '../uploads');
if (!fs.existsSync(uploadsDir)) {
  fs.mkdirSync(uploadsDir, { recursive: true });
}

// Trust proxy for correct req.secure behind ingress
app.set('trust proxy', 1);

// Request ID middleware
app.use((req, res, next) => {
  const requestId = req.header('x-request-id') || uuidv4();
  res.setHeader('x-request-id', requestId);
  req.requestId = requestId;
  next();
});

// Security headers
app.use(helmet());

// CORS
const allowedOrigins = (process.env.CORS_ALLOWED_ORIGINS || '').split(',').filter(Boolean);
app.use(cors({
  origin: (origin, callback) => {
    if (!origin || allowedOrigins.length === 0 || allowedOrigins.includes(origin)) {
      return callback(null, true);
    }
    return callback(new Error('Not allowed by CORS'));
  },
  credentials: true,
  allowedHeaders: ['Origin', 'X-Requested-With', 'Content-Type', 'Accept', 'Authorization', 'x-auth-token', 'x-request-id']
}));

// JSON parser
app.use(express.json());

// Access logs with request id
morgan.token('rid', (req) => req.requestId);
app.use(morgan(':date[iso] :rid :remote-addr :method :url :status :res[content-length] - :response-time ms'));

// HTTPS enforcement in production
if (process.env.NODE_ENV === 'production') {
  app.use((req, res, next) => {
    if (!req.secure) {
      return res.redirect(301, 'https://' + req.headers.host + req.originalUrl);
    }
    next();
  });
}

// Rate limiting
const apiLimiter = rateLimit({ windowMs: 15 * 60 * 1000, max: 100 });
app.use('/api/', apiLimiter);

// Serve static files (for photo uploads)
app.use('/uploads', express.static(uploadsDir));

// Readiness probe
app.get('/ready', async (req, res) => {
  try {
    if (mongoose.connection.readyState !== 1) {
      return res.status(503).json({ ok: false, error: 'mongo_not_connected' });
    }
    await mongoose.connection.db.admin().ping();
    res.json({ ok: true });
  } catch (e) {
    res.status(503).json({ ok: false, error: e.message });
  }
});

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

// Sentry error handler
if (process.env.SENTRY_DSN) {
  app.use(Sentry.Handlers.errorHandler());
}

// Serve static assets in production
if (process.env.NODE_ENV === 'production') {
  app.use(express.static(path.join(__dirname, '../client/build')));
  app.get('*', (req, res) => {
    res.sendFile(path.resolve(__dirname, '../client', 'build', 'index.html'));
  });
}

const PORT = process.env.PORT || 5000;

app.listen(PORT, () => console.log(`Server started on port ${PORT}`));