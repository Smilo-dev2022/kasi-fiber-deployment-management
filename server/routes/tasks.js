const express = require('express');
const { body, validationResult } = require('express-validator');
const Task = require('../models/Task');
const PON = require('../models/PON');
const { auth, authorize } = require('../middleware/auth');

const router = express.Router();

// Default SLA minutes by task type
const DEFAULT_SLA_MINUTES = {
  // Mappings aligned to available task types
  installation: 48 * 60, // PolePlanting
  stringing: 48 * 60,    // Stringing
  cac_check: 24 * 60,    // CAC
  // No defaults for testing, maintenance, documentation, other
};

function getDefaultSlaMinutes(taskType) {
  return DEFAULT_SLA_MINUTES[taskType] || null;
}

// @route   GET api/tasks
// @desc    Get tasks (filtered by user role)
// @access  Private
router.get('/', auth, async (req, res) => {
  try {
    const query = {};
    const { status, type, pon, breached } = req.query;

    // Filter by role
    if (req.user.role === 'site_manager') {
      query.assignedTo = req.user.id;
    } else if (req.user.role === 'project_manager') {
      query.createdBy = req.user.id;
    }

    // Additional filters
    if (status) query.status = status;
    if (type) query.type = type;
    if (pon) query.pon = pon;
    if (breached === 'true') query.breached = true;

    const tasks = await Task.find(query)
      .populate('pon', 'ponId name location')
      .populate('assignedTo', 'name email')
      .populate('createdBy', 'name email')
      .sort({ dueDate: 1 });

    res.json(tasks.map(t => ({
      ...t.toObject(),
      ui: { breachedBadge: t.breached === true }
    })));
  } catch (error) {
    console.error(error.message);
    res.status(500).send('Server Error');
  }
});

// @route   POST api/tasks
// @desc    Create new task
// @access  Private (Project Manager, Admin)
router.post('/', [
  auth,
  authorize('project_manager', 'admin'),
  body('title', 'Title is required').not().isEmpty(),
  body('type', 'Task type is required').isIn(['cac_check', 'stringing', 'installation', 'testing', 'maintenance', 'documentation', 'other']),
  body('pon', 'PON is required').isMongoId(),
  body('assignedTo', 'Assigned user is required').isMongoId(),
  body('dueDate', 'Due date is required').isISO8601()
], async (req, res) => {
  const errors = validationResult(req);
  if (!errors.isEmpty()) {
    return res.status(400).json({ errors: errors.array() });
  }

  try {
    // Verify PON exists and user has access
    const pon = await PON.findById(req.body.pon);
    if (!pon) {
      return res.status(404).json({ message: 'PON not found' });
    }

    if (pon.projectManager.toString() !== req.user.id && req.user.role !== 'admin') {
      return res.status(403).json({ message: 'Access denied' });
    }

    const task = new Task({
      ...req.body,
      createdBy: req.user.id
    });

    await task.save();

    const populatedTask = await Task.findById(task._id)
      .populate('pon', 'ponId name location')
      .populate('assignedTo', 'name email')
      .populate('createdBy', 'name email');

    res.json(populatedTask);
  } catch (error) {
    console.error(error.message);
    res.status(500).send('Server Error');
  }
});

// @route   PUT api/tasks/:id/status
// @desc    Update task status
// @access  Private
router.put('/:id/status', auth, async (req, res) => {
  try {
    const { status } = req.body;
    
    if (!['pending', 'in_progress', 'completed', 'cancelled', 'on_hold'].includes(status)) {
      return res.status(400).json({ message: 'Invalid status' });
    }

    const task = await Task.findById(req.params.id);
    if (!task) {
      return res.status(404).json({ message: 'Task not found' });
    }

    // Check if user can update this task
    if (task.assignedTo.toString() !== req.user.id && 
        task.createdBy.toString() !== req.user.id && 
        req.user.role !== 'admin') {
      return res.status(403).json({ message: 'Access denied' });
    }

    // Check if evidence is required for completion
    if (status === 'completed' && task.evidenceRequired && task.evidencePhotos.length === 0) {
      return res.status(400).json({ message: 'Evidence photos required before marking as completed' });
    }

    task.status = status;
    if (status === 'completed') {
      task.completedDate = new Date();
    } else if (status === 'in_progress' && !task.startDate) {
      task.startDate = new Date();
    }

    await task.save();

    // Update PON progress
    const pon = await PON.findById(task.pon);
    if (pon) {
      await pon.updateProgress();
      await pon.save();
    }

    const updatedTask = await Task.findById(task._id)
      .populate('pon', 'ponId name location')
      .populate('assignedTo', 'name email')
      .populate('createdBy', 'name email');

    res.json(updatedTask);
  } catch (error) {
    console.error(error.message);
    res.status(500).send('Server Error');
  }
});

// @route   PATCH api/tasks/:id
// @desc    Update task fields with SLA semantics
// @access  Private
router.patch('/:id', auth, async (req, res) => {
  try {
    const { status, started_at, completed_at } = req.body || {};

    if (status && !['pending', 'in_progress', 'completed', 'cancelled', 'on_hold'].includes(status)) {
      return res.status(400).json({ message: 'Invalid status' });
    }

    const task = await Task.findById(req.params.id);
    if (!task) {
      return res.status(404).json({ message: 'Task not found' });
    }

    // Permission check
    if (task.assignedTo.toString() !== req.user.id &&
        task.createdBy.toString() !== req.user.id &&
        req.user.role !== 'admin') {
      return res.status(403).json({ message: 'Access denied' });
    }

    // Update status and timestamps
    if (status) {
      // Guard completion requiring evidence
      if (status === 'completed' && task.evidenceRequired && task.evidencePhotos.length === 0) {
        return res.status(400).json({ message: 'Evidence photos required before marking as completed' });
      }
      task.status = status;
    }

    if (started_at) {
      const parsedStart = new Date(started_at);
      if (Number.isNaN(parsedStart.getTime())) {
        return res.status(400).json({ message: 'Invalid started_at' });
      }
      task.startDate = parsedStart;
    } else if (status === 'in_progress' && !task.startDate) {
      task.startDate = new Date();
    }

    if (completed_at) {
      const parsedCompleted = new Date(completed_at);
      if (Number.isNaN(parsedCompleted.getTime())) {
        return res.status(400).json({ message: 'Invalid completed_at' });
      }
      task.completedDate = parsedCompleted;
    } else if (status === 'completed' && !task.completedDate) {
      task.completedDate = new Date();
    }

    // SLA: set due at on start
    const transitionedToInProgress = status === 'in_progress' && (!task.startDate || (started_at != null));
    if (transitionedToInProgress) {
      // Prefer existing explicit slaMinutes, else default by type
      if (typeof task.slaMinutes !== 'number' || task.slaMinutes <= 0) {
        const defaultMinutes = getDefaultSlaMinutes(task.type);
        if (defaultMinutes != null) {
          task.slaMinutes = defaultMinutes;
        }
      }
      if (task.slaMinutes > 0 && task.startDate) {
        task.slaDueAt = new Date(task.startDate.getTime() + task.slaMinutes * 60 * 1000);
      }
    }

    // SLA: mark breach on completion if late
    if (status === 'completed' || task.status === 'completed') {
      if (task.slaDueAt && task.completedDate) {
        task.breached = task.completedDate.getTime() > task.slaDueAt.getTime();
      } else {
        task.breached = false;
      }
    }

    await task.save();

    // Update PON progress
    const pon = await PON.findById(task.pon);
    if (pon) {
      await pon.updateProgress();
      await pon.save();
    }

    const updatedTask = await Task.findById(task._id)
      .populate('pon', 'ponId name location')
      .populate('assignedTo', 'name email')
      .populate('createdBy', 'name email');

    res.json(updatedTask);
  } catch (error) {
    console.error(error.message);
    res.status(500).send('Server Error');
  }
});

module.exports = router;