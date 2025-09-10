const mongoose = require('mongoose');

const PONSchema = new mongoose.Schema({
  ponId: {
    type: String,
    required: true,
    unique: true,
    trim: true
  },
  name: {
    type: String,
    required: true,
    trim: true
  },
  location: {
    type: String,
    required: true,
    trim: true
  },
  coordinates: {
    latitude: Number,
    longitude: Number
  },
  status: {
    type: String,
    enum: ['planned', 'in_progress', 'testing', 'completed', 'maintenance'],
    default: 'planned'
  },
  projectManager: {
    type: mongoose.Schema.Types.ObjectId,
    ref: 'User',
    required: true
  },
  siteManager: {
    type: mongoose.Schema.Types.ObjectId,
    ref: 'User'
  },
  startDate: {
    type: Date,
    required: true
  },
  expectedEndDate: {
    type: Date,
    required: true
  },
  actualEndDate: {
    type: Date
  },
  fiberCount: {
    type: Number,
    required: true,
    min: 1
  },
  splitterCount: {
    type: Number,
    default: 0
  },
  equipment: [{
    name: String,
    model: String,
    serialNumber: String,
    status: {
      type: String,
      enum: ['installed', 'pending', 'faulty', 'replaced'],
      default: 'pending'
    }
  }],
  notes: String,
  progress: {
    type: Number,
    min: 0,
    max: 100,
    default: 0
  }
}, {
  timestamps: true
});

// Auto-compute progress based on related tasks
PONSchema.methods.updateProgress = async function() {
  const Task = mongoose.model('Task');
  const tasks = await Task.find({ pon: this._id });
  
  if (tasks.length === 0) {
    this.progress = 0;
    return;
  }
  
  const completedTasks = tasks.filter(task => task.status === 'completed').length;
  this.progress = Math.round((completedTasks / tasks.length) * 100);
  
  // Auto-update PON status based on progress
  if (this.progress === 0) {
    this.status = 'planned';
  } else if (this.progress === 100) {
    this.status = 'completed';
    this.actualEndDate = new Date();
  } else {
    this.status = 'in_progress';
  }
};

module.exports = mongoose.model('PON', PONSchema);