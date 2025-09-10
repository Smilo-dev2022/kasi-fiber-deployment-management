const mongoose = require('mongoose');

const AssetSchema = new mongoose.Schema({
  code: { type: String, required: true, unique: true, trim: true },
  pon: { type: mongoose.Schema.Types.ObjectId, ref: 'PON' },
  status: { type: String, enum: ['InStock', 'Issued', 'Installed', 'Faulty', 'Retired'], default: 'InStock' },
  type: { type: String, trim: true },
  model: { type: String, trim: true },
  serialNumber: { type: String, trim: true },
  lastScanAction: { type: String, enum: ['ISSUE', 'INSTALL', 'RETURN', 'AUDIT'], default: 'AUDIT' },
  lastScanAt: { type: Date },
  lastScanBy: { type: mongoose.Schema.Types.ObjectId, ref: 'User' }
}, { timestamps: true });

AssetSchema.index({ code: 1, status: 1 });
AssetSchema.index({ pon: 1, status: 1 });

module.exports = mongoose.model('Asset', AssetSchema);

