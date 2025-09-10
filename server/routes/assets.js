const express = require('express');
const { auth, authorize } = require('../middleware/auth');
const Asset = require('../models/Asset');

const router = express.Router();

// GET /api/assets?status=&pon=
router.get('/', [auth, authorize('admin', 'project_manager', 'site_manager')], async (req, res) => {
  try {
    const { status, pon } = req.query;
    const query = {};
    if (status) query.status = status;
    if (pon) query.pon = pon;
    const assets = await Asset.find(query).sort({ createdAt: -1 });
    res.json(assets);
  } catch (error) {
    console.error(error.message);
    res.status(500).send('Server Error');
  }
});

// POST /api/assets/issue  { code, pon }
router.post('/issue', [auth, authorize('admin', 'project_manager')], async (req, res) => {
  try {
    const { code, pon } = req.body;
    if (!code || !pon) return res.status(400).json({ message: 'code and pon are required' });
    const asset = await Asset.findOneAndUpdate({ code }, { $set: { status: 'issued', pon } }, { new: true, upsert: true });
    res.json(asset);
  } catch (error) {
    console.error(error.message);
    res.status(500).send('Server Error');
  }
});

module.exports = router;

