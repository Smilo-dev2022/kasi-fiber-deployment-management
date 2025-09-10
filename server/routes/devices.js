const express = require('express');
const Device = require('../models/Device');
const { auth } = require('../middleware/auth');

const router = express.Router();

router.get('/', auth, async (req, res) => {
  try {
    const { ward, ponId, status, limit = 200 } = req.query;
    const q = {};
    if (ward) q.ward = ward;
    if (ponId) q.ponId = ponId;
    if (status) q.status = status;
    const items = await Device.find(q).sort({ hostname: 1 }).limit(Number(limit));
    res.json(items);
  } catch (e) {
    console.error('Devices list error', e);
    res.status(500).json({ message: 'Server error' });
  }
});

module.exports = router;

