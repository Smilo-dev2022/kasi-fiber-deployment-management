const express = require('express');
const { auth, authorize } = require('../middleware/auth');
const Device = require('../models/Device');

const router = express.Router();

// List devices with filters
router.get('/', auth, async (req, res) => {
  try {
    const { type, tenant, site, ward, pon, status, q } = req.query;
    const query = {};
    if (type) query.type = type;
    if (tenant) query.tenant = tenant;
    if (site) query.site = site;
    if (ward) query.ward = ward;
    if (pon) query.pon = pon;
    if (status) query.status = status;
    if (q) {
      query.$or = [
        { name: new RegExp(q, 'i') },
        { mgmtIp: new RegExp(q, 'i') },
        { serial: new RegExp(q, 'i') }
      ];
    }
    const devices = await Device.find(query).sort({ updatedAt: -1 }).limit(500);
    res.json(devices);
  } catch (err) {
    console.error(err.message);
    res.status(500).send('Server Error');
  }
});

// Create device
router.post('/', auth, authorize('project_manager', 'admin'), async (req, res) => {
  try {
    const device = new Device(req.body);
    await device.save();
    res.json(device);
  } catch (err) {
    console.error(err.message);
    res.status(400).json({ message: 'Invalid device payload' });
  }
});

// Get device
router.get('/:id', auth, async (req, res) => {
  try {
    const device = await Device.findById(req.params.id);
    if (!device) return res.status(404).json({ message: 'Device not found' });
    res.json(device);
  } catch (err) {
    console.error(err.message);
    res.status(404).json({ message: 'Device not found' });
  }
});

// Update device
router.put('/:id', auth, authorize('project_manager', 'admin'), async (req, res) => {
  try {
    const device = await Device.findByIdAndUpdate(req.params.id, { $set: req.body }, { new: true, runValidators: true });
    if (!device) return res.status(404).json({ message: 'Device not found' });
    res.json(device);
  } catch (err) {
    console.error(err.message);
    res.status(400).json({ message: 'Invalid update payload' });
  }
});

// Delete device
router.delete('/:id', auth, authorize('admin'), async (req, res) => {
  try {
    await Device.findByIdAndDelete(req.params.id);
    res.json({ message: 'Deleted' });
  } catch (err) {
    console.error(err.message);
    res.status(404).json({ message: 'Device not found' });
  }
});

module.exports = router;

