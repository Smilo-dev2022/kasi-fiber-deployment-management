const mongoose = require('mongoose');

const AssetSchema = new mongoose.Schema({
  code: { type: String, required: true, unique: true, index: true },
  status: { type: String, enum: ['available', 'issued', 'installed', 'retired'], default: 'available', index: true },
  pon: { type: mongoose.Schema.Types.ObjectId, ref: 'PON', index: true },
  model: String,
  description: String,
}, { timestamps: true });

module.exports = mongoose.model('Asset', AssetSchema);

