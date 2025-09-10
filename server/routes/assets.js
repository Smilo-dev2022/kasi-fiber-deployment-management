const express = require('express');
const { auth, authorize } = require('../middleware/auth');
const Asset = require('../models/Asset');

const router = express.Router();

// GET /assets?status=&pon=
router.get('/', auth, async (req, res) => {
  const { status, pon } = req.query;
  const query = {};
  if (status) query.status = status;
  if (pon) query.pon = pon;
  const assets = await Asset.find(query).sort({ updatedAt: -1 });
  res.json(assets);
});

// Admin list by code
router.get('/:code', [auth, authorize('admin')], async (req, res) => {
  const asset = await Asset.findOne({ code: req.params.code });
  if (!asset) return res.status(404).json({ message: 'Not found' });
  res.json(asset);
});

module.exports = router;

