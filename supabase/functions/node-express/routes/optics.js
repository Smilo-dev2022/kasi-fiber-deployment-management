const express = require('express');
const moment = require('moment');
const OpticalReading = require('../models/OpticalReading');
const PON = require('../models/PON');
const Device = require('../models/Device');
const Incident = require('../models/Incident');
const { auth } = require('../middleware/auth');

const router = express.Router();

// Thresholds per requirements
const THRESHOLDS = {
  to_onu: { targetMin: -25, targetMax: -14, warn: -26, crit: -27 },
  to_olt: { targetMin: -27, targetMax: -15, warn: -28, crit: -29 }
};

// Ingest readings (bulk)
router.post('/ingest', auth, async (req, res) => {
  try {
    const readings = Array.isArray(req.body) ? req.body : [req.body];
    const docs = await OpticalReading.insertMany(readings.map(r => ({ ...r, takenAt: r.takenAt ? new Date(r.takenAt) : new Date() })), { ordered: false });
    res.json({ inserted: docs.length });
  } catch (err) {
    console.error(err.message);
    res.status(400).json({ message: 'Invalid readings' });
  }
});

// Query readings for a PON or ONU
router.get('/', auth, async (req, res) => {
  try {
    const { pon, onuId, device, direction, days = 7 } = req.query;
    const since = moment().subtract(Number(days) || 7, 'days').toDate();
    const query = { takenAt: { $gte: since } };
    if (pon) query.pon = pon;
    if (onuId) query.onuId = onuId;
    if (device) query.device = device;
    if (direction) query.direction = direction;
    const rows = await OpticalReading.find(query).sort({ takenAt: -1 }).limit(5000);
    res.json(rows);
  } catch (err) {
    console.error(err.message);
    res.status(500).send('Server Error');
  }
});

// Drift detection and threshold alerts
router.post('/evaluate', auth, async (req, res) => {
  try {
    const { pon, onuId, days = 1 } = req.body || {};
    const since = moment().subtract(Number(days) || 1, 'days').toDate();
    const query = { takenAt: { $gte: since } };
    if (pon) query.pon = pon;
    if (onuId) query.onuId = onuId;
    const data = await OpticalReading.find(query).sort({ takenAt: 1 });

    // Group by key (direction+onuId or port)
    const groups = new Map();
    for (const r of data) {
      const key = `${r.direction}:${r.onuId || r.port}`;
      const arr = groups.get(key) || [];
      arr.push(r);
      groups.set(key, arr);
    }

    const alerts = [];
    for (const [key, arr] of groups.entries()) {
      const first = arr[0];
      const last = arr[arr.length - 1];
      const delta = last.powerDbm - first.powerDbm; // positive means improved
      const dir = last.direction;
      const th = THRESHOLDS[dir];
      if (!th) continue;
      let severity = null;
      if (last.powerDbm <= th.crit) severity = 'critical';
      else if (last.powerDbm <= th.warn) severity = 'major';
      if (Math.abs(delta) >= 3) {
        severity = severity || 'major';
      }
      if (severity) {
        alerts.push({ key, last: last.powerDbm, delta, severity, direction: dir, onuId: last.onuId });
      }
    }

    res.json({ alerts });
  } catch (err) {
    console.error(err.message);
    res.status(500).send('Server Error');
  }
});

module.exports = router;

