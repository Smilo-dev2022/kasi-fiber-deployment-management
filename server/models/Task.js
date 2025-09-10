const mongoose = require('mongoose');
const { computeSlaSettings } = require('../config/sla');

const TaskSchema = new mongoose.Schema({
  title: {
    type: String,
    required: true,
    trim: true
  },
  description: {
    type: String,
    trim: true
  },
  type: {
    type: String,
    enum: ['cac_check', 'stringing', 'installation', 'testing', 'maintenance', 'documentation', 'other'],
    required: true
  },
  pon: {
    type: mongoose.Schema.Types.ObjectId,
    ref: 'PON',
    required: true
  },
  assignedTo: {
    type: mongoose.Schema.Types.ObjectId,
    ref: 'User',
    required: true
  },
  createdBy: {
    type: mongoose.Schema.Types.ObjectId,
    ref: 'User',
    required: true
  },
  priority: {
    type: String,
    enum: ['low', 'medium', 'high', 'critical'],
    default: 'medium'
  },
  status: {
    type: String,
    enum: ['pending', 'in_progress', 'completed', 'cancelled', 'on_hold'],
    default: 'pending'
  },
  startDate: {
    type: Date
  },
  dueDate: {
    type: Date,
    required: true
  },
  completedDate: {
    type: Date
  },
  estimatedHours: {
    type: Number,
    min: 0
  },
  actualHours: {
    type: Number,
    min: 0
  },
  sla: {
    ackBy: Date,
    completeBy: Date,
    ackedAt: Date,
    breachedAck: {
      type: Boolean,
      default: false
    },
    breachedCompletion: {
      type: Boolean,
      default: false
    },
    lastAlertedAt: Date
  },
  evidenceRequired: {
    type: Boolean,
    default: false
  },
  evidencePhotos: [{
    filename: String,
    originalName: String,
    uploadDate: {
      type: Date,
      default: Date.now
    },
    uploadedBy: {
      type: mongoose.Schema.Types.ObjectId,
      ref: 'User'
    },
    metadata: {
      exifDate: Date,
      gpsLatitude: Number,
      gpsLongitude: Number,
      gpsAccuracy: Number,
      distanceMeters: Number,
      allowedRadiusMeters: Number,
      exifError: Boolean
    },
    gpsValid: Boolean
  }],
  notes: String,
  dependencies: [{
    type: mongoose.Schema.Types.ObjectId,
    ref: 'Task'
  }]
}, {
  timestamps: true
});

// Compute SLA deadlines
TaskSchema.methods.computeSlaDeadlines = function() {
  const { ackHours, completionHours } = computeSlaSettings(this.type, this.priority);

  const createdAtDate = this.createdAt ? new Date(this.createdAt) : new Date();
  const computedAckBy = new Date(createdAtDate.getTime() + ackHours * 60 * 60 * 1000);
  const computedCompleteBy = new Date(createdAtDate.getTime() + completionHours * 60 * 60 * 1000);

  const finalCompleteBy = this.dueDate ? new Date(Math.min(computedCompleteBy.getTime(), new Date(this.dueDate).getTime())) : computedCompleteBy;

  if (!this.sla) this.sla = {};
  if (!this.sla.ackBy) this.sla.ackBy = computedAckBy;
  if (!this.sla.completeBy) this.sla.completeBy = finalCompleteBy;
};

// Check if task can be started (dependencies completed)
TaskSchema.methods.canStart = async function() {
  if (this.dependencies.length === 0) return true;
  
  const Task = mongoose.model('Task');
  const deps = await Task.find({ 
    _id: { $in: this.dependencies },
    status: { $ne: 'completed' }
  });
  
  return deps.length === 0;
};

// Auto-complete task when evidence is provided (if required)
TaskSchema.pre('save', function(next) {
  // Compute SLA on create or when related fields change
  if (this.isNew || this.isModified('type') || this.isModified('priority') || this.isModified('dueDate')) {
    this.computeSlaDeadlines();
  }

  // Set ackedAt on first move to in_progress
  if (this.isModified('status') && this.status === 'in_progress' && (!this.sla || !this.sla.ackedAt)) {
    if (!this.sla) this.sla = {};
    this.sla.ackedAt = new Date();
  }

  if (this.evidenceRequired && this.evidencePhotos.length > 0 && this.status === 'in_progress') {
    this.status = 'completed';
    this.completedDate = new Date();
  }
  next();
});

module.exports = mongoose.model('Task', TaskSchema);