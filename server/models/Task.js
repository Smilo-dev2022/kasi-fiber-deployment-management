const mongoose = require('mongoose');

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
    }
  }],
  notes: String,
  dependencies: [{
    type: mongoose.Schema.Types.ObjectId,
    ref: 'Task'
  }]
}, {
  timestamps: true
});

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
  if (this.evidenceRequired && this.evidencePhotos.length > 0 && this.status === 'in_progress') {
    this.status = 'completed';
    this.completedDate = new Date();
  }
  next();
});

module.exports = mongoose.model('Task', TaskSchema);
// Indexes for speed
TaskSchema.index({ pon: 1 });
TaskSchema.index({ status: 1 });