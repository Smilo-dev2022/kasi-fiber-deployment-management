const mongoose = require('mongoose');

const IncidentSchema = new mongoose.Schema({
  device: { type: mongoose.Schema.Types.ObjectId, ref: 'Device', index: true },
  deviceHostname: { type: String, index: true },
  eventType: { type: String, enum: ['down', 'up', 'optical_low', 'clear', 'unknown'], index: true },
  severity: { type: String, enum: ['p1', 'p2', 'p3', 'p4'], index: true },
  status: { type: String, enum: ['open', 'ack', 'resolved', 'suppressed'], default: 'open', index: true },
  message: { type: String },
  dedupKey: { type: String, required: true, index: true },
  openedAt: { type: Date, required: true },
  acknowledgedAt: { type: Date },
  resolvedAt: { type: Date },
  mttrMs: { type: Number, index: true },
  mttdMs: { type: Number },
  vendor: { type: String },
  raw: { type: Object },
  ward: { type: String, index: true },
  ponId: { type: String, index: true },
}, { timestamps: true });

IncidentSchema.index({ dedupKey: 1, status: 1 });
IncidentSchema.index({ ward: 1, status: 1 });
IncidentSchema.index({ ponId: 1, status: 1 });

module.exports = mongoose.model('Incident', IncidentSchema);

