const mongoose = require('mongoose');

// Optical readings for OLT ports and ONUs/ONTs
const OpticalReadingSchema = new mongoose.Schema({
  pon: { type: mongoose.Schema.Types.ObjectId, ref: 'PON', index: true },
  device: { type: mongoose.Schema.Types.ObjectId, ref: 'Device', index: true },
  port: { type: String }, // e.g., 1/1/1 or PON1
  onuId: { type: String },
  direction: { type: String, enum: ['to_onu', 'to_olt'], required: true },
  powerDbm: { type: Number, required: true },
  oltSlot: String,
  oltPort: String,
  vendor: String,
  model: String,
  takenAt: { type: Date, default: Date.now, index: true },
  source: { type: String, enum: ['NMS', 'field', 'import'], default: 'NMS' },
  meta: {},
}, { timestamps: true });

OpticalReadingSchema.index({ pon: 1, takenAt: -1 });
OpticalReadingSchema.index({ onuId: 1, takenAt: -1 });

module.exports = mongoose.model('OpticalReading', OpticalReadingSchema);

