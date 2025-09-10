const mongoose = require('mongoose');

const StateLogSchema = new mongoose.Schema({
  entityType: { type: String, enum: ['PON', 'Task', 'Photo', 'Asset'], required: true },
  entityId: { type: mongoose.Schema.Types.ObjectId, required: true },
  before: { type: mongoose.Schema.Types.Mixed },
  after: { type: mongoose.Schema.Types.Mixed },
  actor: { type: mongoose.Schema.Types.ObjectId, ref: 'User' },
  context: { type: String }
}, { timestamps: true });

StateLogSchema.index({ entityType: 1, entityId: 1, createdAt: -1 });

module.exports = mongoose.model('StateLog', StateLogSchema);

