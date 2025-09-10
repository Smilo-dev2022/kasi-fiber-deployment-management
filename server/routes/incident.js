const express = require('express');
const Incident = require('../models/Incident');
const Device = require('../models/Device');
const { auth, authorize } = require('../middleware/auth');

const router = express.Router();

// Minimal incidents list for dashboards
router.get('/', auth, async (req, res) => {
  try {
    const { status, severity, ward, ponId, limit = 100 } = req.query;
    const q = {};
    if (status) q.status = status;
    if (severity) q.severity = severity;
    if (ward) q.ward = ward;
    if (ponId) q.ponId = ponId;
    const items = await Incident.find(q).sort({ createdAt: -1 }).limit(Number(limit));
    res.json(items);
  } catch (e) {
    console.error('Incidents list error', e);
    res.status(500).json({ message: 'Server error' });
  }
});

module.exports = router;

