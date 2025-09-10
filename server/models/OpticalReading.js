const mongoose = require('mongoose');

const OpticalReadingSchema = new mongoose.Schema({
  device: { type: mongoose.Schema.Types.ObjectId, ref: 'Device', index: true },
  deviceHostname: { type: String, index: true },
  port: { type: String, index: true },
  onuId: { type: String, index: true },
  direction: { type: String, enum: ['rx', 'tx'], default: 'rx' },
  powerDbm: { type: Number, required: true },
  baselineDbm: { type: Number },
  driftDb: { type: Number, index: true },
  takenAt: { type: Date, required: true, index: true },
  source: { type: String, enum: ['nms', 'field', 'seed'], default: 'nms' },
  ward: { type: String, index: true },
  ponId: { type: String, index: true },
  metadata: { type: Object },
}, { timestamps: true });

OpticalReadingSchema.index({ deviceHostname: 1, port: 1, onuId: 1, takenAt: -1 });

module.exports = mongoose.model('OpticalReading', OpticalReadingSchema);

