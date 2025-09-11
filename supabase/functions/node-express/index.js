const express = require('express');
const cors = require('cors');
const path = require('path');
require('dotenv').config();

const connectDB = require('./config/database');
const { startSlaMonitor } = require('./jobs/slaMonitor');

const app = express();

// Connect Database
connectDB();

// Init Middleware
app.use(express.json({ extended: false }));
app.use(cors());

// Serve static files (for photo uploads)
app.use('/uploads', express.static(path.join(__dirname, '../uploads')));

// Define Routes
app.use('/api/auth', require('./routes/auth'));
app.use('/api/users', require('./routes/users'));
app.use('/api/pons', require('./routes/pons'));
app.use('/api/tasks', require('./routes/tasks'));
app.use('/api/devices', require('./routes/devices'));
app.use('/api/incidents', require('./routes/incidents'));
app.use('/api/optics', require('./routes/optics'));
app.use('/api/nms', require('./routes/nmsWebhook'));
app.use('/api/cac', require('./routes/cac'));
app.use('/api/stringing', require('./routes/stringing'));
app.use('/api/photos', require('./routes/photos'));
app.use('/api/smme', require('./routes/smme'));
app.use('/api/stock', require('./routes/stock'));
app.use('/api/invoicing', require('./routes/invoicing'));
app.use('/api/reports', require('./routes/reports'));

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