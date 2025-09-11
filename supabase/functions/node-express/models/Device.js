const mongoose = require('mongoose');

// Device covers OLTs, ONUs/ONTs, switches, routers, splitters as logical ports, UPS, generators
// We keep generic fields and allow type-specific metadata in nested objects
const DeviceSchema = new mongoose.Schema({
  tenant: { type: String, index: true },
  site: { type: String, index: true },
  ward: { type: String, index: true },
  type: {
    type: String,
    enum: ['OLT', 'ONU', 'ONT', 'SWITCH', 'ROUTER', 'SPLITTER', 'UPS', 'GENERATOR', 'BATTERY', 'PDU', 'CPE', 'WIFI'],
    required: true,
    index: true
  },
  vendor: String,
  model: String,
  serial: { type: String, index: true },
  mgmtIp: { type: String, index: true },
  name: { type: String, trim: true },
  pon: { type: mongoose.Schema.Types.ObjectId, ref: 'PON', index: true },
  oltChassis: String,
  oltSlot: String,
  oltPort: String,
  onuId: String,
  status: { type: String, enum: ['up', 'down', 'degraded', 'maintenance'], default: 'up', index: true },
  lastSeenAt: { type: Date },
  // Inventory/SoT linkage keys (e.g., NetBox IDs)
  sot:
    {
      netboxId: String,
      rack: String,
      position: String
    },
  // Telemetry last snapshot for quick list views
  snapshot: {
    cpu: Number,
    memory: Number,
    temperatureC: Number,
    rxErrors: Number,
    txErrors: Number,
    uptimeSeconds: Number
  },
  // Location for maps
  location: {
    latitude: Number,
    longitude: Number
  }
}, { timestamps: true });

DeviceSchema.index({ type: 1, mgmtIp: 1 });
DeviceSchema.index({ tenant: 1, site: 1, type: 1 });

module.exports = mongoose.model('Device', DeviceSchema);

