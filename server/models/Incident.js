const mongoose = require('mongoose');

// Incident lifecycle for network faults and maintenance
const IncidentSchema = new mongoose.Schema({
  title: { type: String, required: true },
  description: String,
  priority: { type: String, enum: ['P1', 'P2', 'P3', 'P4'], required: true, index: true },
  category: {
    type: String,
    enum: ['device_down', 'los', 'uplink_down', 'optical_low_power', 'interface_flaps', 'high_cpu', 'power_loss', 'environmental', 'config_drift', 'maintenance', 'other'],
    default: 'other'
  },
  status: { type: String, enum: ['open', 'acknowledged', 'in_progress', 'monitoring', 'resolved', 'closed'], default: 'open', index: true },
  tenant: { type: String, index: true },
  ward: { type: String, index: true },
  site: { type: String, index: true },
  pon: { type: mongoose.Schema.Types.ObjectId, ref: 'PON', index: true },
  device: { type: mongoose.Schema.Types.ObjectId, ref: 'Device', index: true },
  relatedOnuId: String,
  nmsEventId: String, // correlation key from NMS
  nmsSource: String,  // LibreNMS, Zabbix
  signals: [{
    key: String,      // e.g., olt_port, onu_id, alarm
    value: String,
    ts: { type: Date, default: Date.now }
  }],
  openedAt: { type: Date, default: Date.now },
  acknowledgedAt: { type: Date },
  resolvedAt: { type: Date },
  closedAt: { type: Date },
  // SLA fields
  respondBy: { type: Date },
  restoreBy: { type: Date },
  breachedRespond: { type: Boolean, default: false },
  breachedRestore: { type: Boolean, default: false },
  // Closure requirements
  rootCause: String,
  fixCode: { type: String, enum: ['cleaned_connector', 'reterminated', 'replaced_pigtail', 'replaced_sfp', 'rebooted', 'failover', 'config_fix', 'firmware_upgrade', 'power_restored', 'other'], default: 'other' },
  closureNotes: String,
  closurePhotos: [{ filename: String, url: String }],
  closureGps: {
    latitude: Number,
    longitude: Number,
    capturedAt: Date
  }
}, { timestamps: true });

IncidentSchema.index({ status: 1, priority: 1 });
IncidentSchema.index({ nmsSource: 1, nmsEventId: 1 }, { unique: false });

module.exports = mongoose.model('Incident', IncidentSchema);

