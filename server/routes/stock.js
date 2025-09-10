const express = require('express');
const { body, validationResult } = require('express-validator');
const { auth } = require('../middleware/auth');
const { v4: uuidv4 } = require('uuid');
const QRCode = require('qrcode');
const StockItem = require('../models/StockItem');

const router = express.Router();

// Stock management and QR labels + custody logs

// @route   GET api/stock
// @desc    Get stock items
// @access  Private
router.get('/', auth, async (req, res) => {
	try {
		const { type, status } = req.query;
		const query = {};
		if (type) query.type = type;
		if (status) query.status = status;
		const items = await StockItem.find(query).sort({ createdAt: -1 });
		res.json(items);
	} catch (error) {
		console.error(error.message);
		res.status(500).send('Server Error');
	}
});

// @route   POST api/stock/qrcode
// @desc    Generate QR code label for a stock item
// @access  Private
router.post('/qrcode', [
	auth,
	body('type').isIn(['pole', 'drum', 'bracket', 'other']).withMessage('Invalid type'),
	body('sku').optional().isString(),
	body('description').optional().isString()
], async (req, res) => {
	const errors = validationResult(req);
	if (!errors.isEmpty()) {
		return res.status(400).json({ errors: errors.array() });
	}

	try {
		const { type, sku, description } = req.body;
		const qrId = uuidv4();
		const labelPayload = { qrId, type, sku };
		const uri = await QRCode.toDataURL(JSON.stringify(labelPayload), { width: 300, margin: 1 });

		const item = new StockItem({ qrId, type, sku, description, status: 'in' });
		await item.save();

		res.json({ qrId, labelDataUrl: uri, item });
	} catch (error) {
		console.error(error.message);
		res.status(500).send('Server Error');
	}
});

// @route   POST api/stock/scan
// @desc    Scan in/out and record custody
// @access  Private
router.post('/scan', [
	auth,
	body('qrId', 'qrId is required').not().isEmpty(),
	body('action').isIn(['scan_in', 'scan_out']).withMessage('Invalid action'),
	body('holderType').optional().isString(),
	body('holderId').optional().isString(),
	body('location').optional().isObject()
], async (req, res) => {
	const errors = validationResult(req);
	if (!errors.isEmpty()) {
		return res.status(400).json({ errors: errors.array() });
	}

	try {
		const { qrId, action, holderType, holderId, location } = req.body;
		const item = await StockItem.findOne({ qrId });
		if (!item) {
			return res.status(404).json({ message: 'Item not found' });
		}

		item.status = action === 'scan_in' ? 'in' : 'out';
		item.currentHolder = { holderType, holderId };
		item.custodyLogs.push({ action, performedBy: req.user.id, location, holderType, holderId });
		await item.save();

		res.json({ message: 'Scan recorded', item });
	} catch (error) {
		console.error(error.message);
		res.status(500).send('Server Error');
	}
});

// @route   GET api/stock/item/:qrId
// @desc    Get single item by qrId
// @access  Private
router.get('/item/:qrId', auth, async (req, res) => {
	try {
		const item = await StockItem.findOne({ qrId: req.params.qrId });
		if (!item) return res.status(404).json({ message: 'Item not found' });
		res.json(item);
	} catch (error) {
		console.error(error.message);
		res.status(500).send('Server Error');
	}
});

module.exports = router;