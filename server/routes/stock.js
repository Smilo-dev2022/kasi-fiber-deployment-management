const express = require('express');
const { auth } = require('../middleware/auth');
const Asset = require('../models/Asset');

const router = express.Router();

// Stock management module

// @route   GET api/stock
// @desc    Get stock items
// @access  Private
router.get('/', auth, async (req, res) => {
  try {
    const { status, pon } = req.query;
    const query = {};
    if (status) query.status = status;
    if (pon) query.pon = pon;
    const assets = await Asset.find(query).sort({ updatedAt: -1 });
    res.json(assets);
  } catch (error) {
    console.error(error.message);
    res.status(500).send('Server Error');
  }
});

// @route   POST api/stock
// @desc    Add stock item
// @access  Private
router.post('/', auth, async (req, res) => {
  try {
    const { code, type, model, serialNumber } = req.body;
    if (!code) return res.status(400).json({ message: 'code required' });
    const existing = await Asset.findOne({ code });
    if (existing) return res.status(400).json({ message: 'Asset code exists' });
    const asset = await Asset.create({ code, type, model, serialNumber });
    res.json(asset);
  } catch (error) {
    console.error(error.message);
    res.status(500).send('Server Error');
  }
});

// Tie stock issue to asset scan ISSUE action
router.post('/:code/scan', auth, async (req, res) => {
  try {
    const { action, pon } = req.body;
    const asset = await Asset.findOne({ code: req.params.code });
    if (!asset) return res.status(404).json({ message: 'Asset not found' });

    if (action === 'ISSUE') {
      asset.status = 'Issued';
      asset.pon = pon || asset.pon;
    } else if (action === 'INSTALL') {
      if (asset.status !== 'Issued') {
        return res.status(400).json({ message: 'Asset must be Issued before INSTALL' });
      }
      asset.status = 'Installed';
    } else if (action === 'RETURN') {
      asset.status = 'InStock';
      asset.pon = undefined;
    }
    asset.lastScanAction = action;
    asset.lastScanAt = new Date();
    asset.lastScanBy = req.user.id;
    await asset.save();
    res.json(asset);
  } catch (error) {
    console.error(error.message);
    res.status(500).send('Server Error');
  }
});

module.exports = router;