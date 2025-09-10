const mongoose = require('mongoose');

const CustodyLogSchema = new mongoose.Schema({
	action: {
		type: String,
		enum: ['scan_in', 'scan_out'],
		required: true
	},
	performedBy: { type: mongoose.Schema.Types.ObjectId, ref: 'User', required: true },
	performedAt: { type: Date, default: Date.now },
	location: {
		latitude: Number,
		longitude: Number
	},
	holderType: String,
	holderId: String
}, { _id: false });

const StockItemSchema = new mongoose.Schema({
	qrId: { type: String, required: true, unique: true },
	type: { type: String, enum: ['pole', 'drum', 'bracket', 'other'], required: true },
	sku: { type: String },
	description: { type: String },
	status: { type: String, enum: ['in', 'out'], default: 'in' },
	currentHolder: {
		holderType: String,
		holderId: String
	},
	custodyLogs: [CustodyLogSchema]
}, { timestamps: true });

module.exports = mongoose.model('StockItem', StockItemSchema);

