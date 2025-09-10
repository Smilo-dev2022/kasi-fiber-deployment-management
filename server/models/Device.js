const mongoose = require('mongoose');

const DeviceSchema = new mongoose.Schema({
  hostname: { type: String, required: true, index: true, unique: true, trim: true },
  name: { type: String, trim: true },
  ward: { type: String, index: true },
  ponId: { type: String, index: true },
  vendor: { type: String, enum: ['unknown', 'zte', 'huawei', 'calix', 'nokianokia', 'other'], default: 'unknown' },
  ipAddress: { type: String },
  gps: {
    latitude: { type: Number },
    longitude: { type: Number },
  },
  metadata: { type: Object },
  status: { type: String, enum: ['up', 'down', 'degraded', 'unknown'], default: 'unknown', index: true },
  lastSeenAt: { type: Date },
}, { timestamps: true });

module.exports = mongoose.model('Device', DeviceSchema);

