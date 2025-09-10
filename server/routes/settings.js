const express = require('express');
const Setting = require('../models/Setting');
const { auth, authorize } = require('../middleware/auth');

const router = express.Router();

const DEFAULT_SLA = {
  cac_check: 48,
  stringing: 72,
  installation: 96,
  testing: 24,
  documentation: 24
};

async function getSlaMap() {
  const doc = await Setting.findOne({ key: 'sla' });
  return doc ? doc.value : DEFAULT_SLA;
}

// GET current SLAs
router.get('/sla', [auth, authorize('admin', 'project_manager')], async (req, res) => {
  try {
    const sla = await getSlaMap();
    res.json(sla);
  } catch (error) {
    console.error(error.message);
    res.status(500).send('Server Error');
  }
});

// PUT update SLAs
router.put('/sla', [auth, authorize('admin')], async (req, res) => {
  try {
    const incoming = req.body || {};
    const existing = await getSlaMap();
    const merged = { ...existing, ...incoming };
    const doc = await Setting.findOneAndUpdate(
      { key: 'sla' },
      { $set: { value: merged } },
      { upsert: true, new: true }
    );
    res.json(doc.value);
  } catch (error) {
    console.error(error.message);
    res.status(500).send('Server Error');
  }
});

module.exports = router;

