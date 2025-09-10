const mongoose = require('mongoose');

const AssetSchema = new mongoose.Schema({
  assetType: {
    type: String,
    enum: ['pole', 'drum'],
    required: true
  },
  assetId: {
    type: String,
    required: true,
    unique: true
  },
  pon: {
    type: mongoose.Schema.Types.ObjectId,
    ref: 'PON'
  },
  status: {
    type: String,
    enum: ['in_stock', 'deployed', 'retired'],
    default: 'in_stock'
  },
  qr: {
    data: String, // content encoded
    imageDataUrl: String // generated QR as data URL (optional)
  },
  metadata: mongoose.Schema.Types.Mixed
}, {
  timestamps: true
});

module.exports = mongoose.model('Asset', AssetSchema);

