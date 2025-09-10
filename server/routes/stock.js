const express = require('express');
const { auth } = require('../middleware/auth');
const QRCode = require('qrcode');
const Asset = require('../models/Asset');

const router = express.Router();

// Stock management module

// @route   GET api/stock
// @desc    Get stock items
// @access  Private
router.get('/', auth, async (req, res) => {
  try {
    const assets = await Asset.find().sort({ createdAt: -1 });
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
    const { assetType, assetId, pon, metadata } = req.body;

    const data = `asset:${assetType}:${assetId}`;
    const imageDataUrl = await QRCode.toDataURL(data, { errorCorrectionLevel: 'M' });

    const asset = new Asset({ assetType, assetId, pon, metadata, qr: { data, imageDataUrl } });
    await asset.save();
    res.json(asset);
  } catch (error) {
    console.error(error.message);
    res.status(500).send('Server Error');
  }
});

// @route   GET api/stock/:assetId/qr
// @desc    Get QR code image for asset
// @access  Private
router.get('/:assetId/qr', auth, async (req, res) => {
  try {
    const asset = await Asset.findOne({ assetId: req.params.assetId });
    if (!asset) return res.status(404).json({ message: 'Asset not found' });
    if (!asset.qr?.imageDataUrl) return res.status(404).json({ message: 'QR not available' });
    const base64 = asset.qr.imageDataUrl.split(',')[1];
    const img = Buffer.from(base64, 'base64');
    res.setHeader('Content-Type', 'image/png');
    res.send(img);
  } catch (error) {
    console.error(error.message);
    res.status(500).send('Server Error');
  }
});

module.exports = router;