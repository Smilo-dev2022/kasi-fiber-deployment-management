const mongoose = require('mongoose');

const MaintenanceWindowSchema = new mongoose.Schema({
  title: { type: String, required: true },
  description: { type: String },
  approved: { type: Boolean, default: false, index: true },
  startAt: { type: Date, required: true, index: true },
  endAt: { type: Date, required: true, index: true },
  // Target selectors
  deviceHostnames: [{ type: String, index: true }],
  wards: [{ type: String, index: true }],
  ponIds: [{ type: String, index: true }],
  // Checks
  preChecksDone: { type: Boolean, default: false },
  postChecksDone: { type: Boolean, default: false },
  createdBy: { type: mongoose.Schema.Types.ObjectId, ref: 'User' },
}, { timestamps: true });

MaintenanceWindowSchema.index({ approved: 1, startAt: 1, endAt: 1 });

module.exports = mongoose.model('MaintenanceWindow', MaintenanceWindowSchema);

