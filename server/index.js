const express = require('express');
const cors = require('cors');
const helmet = require('helmet');
const path = require('path');
require('dotenv').config();

const connectDB = require('./config/database');
const { startSlaMonitor } = require('./jobs/slaMonitor');

const app = express();

// Connect Database
connectDB();

// Init Middleware
app.use(helmet({
  contentSecurityPolicy: false,
}));
app.use(express.json({ extended: false }));
const allowOrigins = (process.env.CORS_ALLOW_ORIGINS || '').split(',').map(s => s.trim()).filter(Boolean);
app.use(cors({
  origin: allowOrigins.length ? allowOrigins : '*',
  credentials: true,
}));

// Serve static files (for photo uploads)
app.use('/uploads', express.static(path.join(__dirname, '../uploads')));

// Define Routes (legacy). Tighten or disable specific routes via env
const legacyEnabled = (name) => (process.env[`LEGACY_${name}_ENABLED`] || 'false').toLowerCase() === 'true';
if (legacyEnabled('AUTH')) app.use('/api/auth', require('./routes/auth'));
if (legacyEnabled('USERS')) app.use('/api/users', require('./routes/users'));
if (legacyEnabled('PONS')) app.use('/api/pons', require('./routes/pons'));
if (legacyEnabled('TASKS')) app.use('/api/tasks', require('./routes/tasks'));
if (legacyEnabled('DEVICES')) app.use('/api/devices', require('./routes/devices'));
if (legacyEnabled('INCIDENTS')) app.use('/api/incidents', require('./routes/incidents'));
if (legacyEnabled('OPTICS')) app.use('/api/optics', require('./routes/optics'));
if (legacyEnabled('NMS')) app.use('/api/nms', require('./routes/nmsWebhook'));
if (legacyEnabled('CAC')) app.use('/api/cac', require('./routes/cac'));
if (legacyEnabled('STRINGING')) app.use('/api/stringing', require('./routes/stringing'));
if (legacyEnabled('PHOTOS')) app.use('/api/photos', require('./routes/photos'));
if (legacyEnabled('SMME')) app.use('/api/smme', require('./routes/smme'));
if (legacyEnabled('STOCK')) app.use('/api/stock', require('./routes/stock'));
if (legacyEnabled('INVOICING')) app.use('/api/invoicing', require('./routes/invoicing'));
if (legacyEnabled('REPORTS')) app.use('/api/reports', require('./routes/reports'));

// Serve static assets in production
if (process.env.NODE_ENV === 'production') {
  app.use(express.static(path.join(__dirname, '../client/build')));
  
  app.get('*', (req, res) => {
    res.sendFile(path.resolve(__dirname, '../client', 'build', 'index.html'));
  });
}

const PORT = process.env.PORT || 5000;

app.listen(PORT, () => console.log(`Server started on port ${PORT}`));
// Start background jobs
if (process.env.DISABLE_SLA_MONITOR !== 'true') {
  const intervalMs = Number(process.env.SLA_MONITOR_INTERVAL_MS || 60000);
  startSlaMonitor(intervalMs);
}