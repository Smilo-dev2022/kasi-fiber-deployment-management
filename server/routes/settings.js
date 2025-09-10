const express = require('express');
const { body, validationResult } = require('express-validator');
const { auth, authorize } = require('../middleware/auth');
const Setting = require('../models/Setting');

const router = express.Router();

// Get all settings (admin)
router.get('/', [auth, authorize('admin')], async (req, res) => {
  const settings = await Setting.find({}).sort({ key: 1 });
  res.json(settings);
});

// Upsert SLA config map
router.put('/sla', [auth, authorize('admin'), body('map').isObject()], async (req, res) => {
  const errors = validationResult(req);
  if (!errors.isEmpty()) return res.status(400).json({ errors: errors.array() });
  const doc = await Setting.findOneAndUpdate(
    { key: 'sla.map' },
    { $set: { value: req.body.map } },
    { new: true, upsert: true }
  );
  res.json(doc);
});

module.exports = router;

