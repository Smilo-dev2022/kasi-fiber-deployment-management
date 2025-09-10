const express = require('express');
const { body, validationResult } = require('express-validator');
const PON = require('../models/PON');
const Task = require('../models/Task');
const { auth, authorize } = require('../middleware/auth');

const router = express.Router();

// @route   GET api/pons
// @desc    Get all PONs
// @access  Private
router.get('/', auth, async (req, res) => {
  try {
    const query = {};
    
    // Filter by role
    if (req.user.role === 'site_manager') {
      query.siteManager = req.user.id;
    } else if (req.user.role === 'project_manager') {
      query.projectManager = req.user.id;
    }

    const pons = await PON.find(query)
      .populate('projectManager', 'name email')
      .populate('siteManager', 'name email')
      .sort({ createdAt: -1 });

    res.json(pons);
  } catch (error) {
    console.error(error.message);
    res.status(500).send('Server Error');
  }
});

// @route   GET api/pons/:id
// @desc    Get PON by ID
// @access  Private
router.get('/:id', auth, async (req, res) => {
  try {
    const pon = await PON.findById(req.params.id)
      .populate('projectManager', 'name email phone')
      .populate('siteManager', 'name email phone');

    if (!pon) {
      return res.status(404).json({ message: 'PON not found' });
    }

    // Check authorization
    if (req.user.role === 'site_manager' && pon.siteManager?.toString() !== req.user.id) {
      return res.status(403).json({ message: 'Access denied' });
    }
    if (req.user.role === 'project_manager' && pon.projectManager.toString() !== req.user.id) {
      return res.status(403).json({ message: 'Access denied' });
    }

    // Get related tasks
    const tasks = await Task.find({ pon: pon._id })
      .populate('assignedTo', 'name email')
      .sort({ createdAt: -1 });

    res.json({ pon, tasks });
  } catch (error) {
    console.error(error.message);
    if (error.kind === 'ObjectId') {
      return res.status(404).json({ message: 'PON not found' });
    }
    res.status(500).send('Server Error');
  }
});

// @route   POST api/pons
// @desc    Create new PON
// @access  Private (Project Manager, Admin)
router.post('/', [
  auth,
  authorize('project_manager', 'admin'),
  body('ponId', 'PON ID is required').not().isEmpty(),
  body('name', 'Name is required').not().isEmpty(),
  body('location', 'Location is required').not().isEmpty(),
  body('startDate', 'Start date is required').isISO8601(),
  body('expectedEndDate', 'Expected end date is required').isISO8601(),
  body('fiberCount', 'Fiber count must be a positive number').isInt({ min: 1 })
], async (req, res) => {
  const errors = validationResult(req);
  if (!errors.isEmpty()) {
    return res.status(400).json({ errors: errors.array() });
  }

  try {
    const {
      ponId,
      name,
      location,
      coordinates,
      siteManager,
      startDate,
      expectedEndDate,
      fiberCount,
      splitterCount,
      equipment,
      notes
    } = req.body;

    // Check if PON ID already exists
    const existingPON = await PON.findOne({ ponId });
    if (existingPON) {
      return res.status(400).json({ message: 'PON ID already exists' });
    }

    const pon = new PON({
      ponId,
      name,
      location,
      coordinates,
      projectManager: req.user.id,
      siteManager,
      startDate,
      expectedEndDate,
      fiberCount,
      splitterCount,
      equipment,
      notes
    });

    await pon.save();
    
    const populatedPON = await PON.findById(pon._id)
      .populate('projectManager', 'name email')
      .populate('siteManager', 'name email');

    res.json(populatedPON);
  } catch (error) {
    console.error(error.message);
    res.status(500).send('Server Error');
  }
});

// @route   PUT api/pons/:id
// @desc    Update PON
// @access  Private (Project Manager, Admin)
router.put('/:id', [
  auth,
  authorize('project_manager', 'admin')
], async (req, res) => {
  try {
    let pon = await PON.findById(req.params.id);

    if (!pon) {
      return res.status(404).json({ message: 'PON not found' });
    }

    // Check if user owns this PON
    if (pon.projectManager.toString() !== req.user.id && req.user.role !== 'admin') {
      return res.status(403).json({ message: 'Access denied' });
    }

    const updateFields = { ...req.body };
    delete updateFields.projectManager; // Prevent changing project manager

    pon = await PON.findByIdAndUpdate(
      req.params.id,
      { $set: updateFields },
      { new: true, runValidators: true }
    ).populate('projectManager', 'name email')
     .populate('siteManager', 'name email');

    res.json(pon);
  } catch (error) {
    console.error(error.message);
    if (error.kind === 'ObjectId') {
      return res.status(404).json({ message: 'PON not found' });
    }
    res.status(500).send('Server Error');
  }
});

// @route   PUT api/pons/:id/progress
// @desc    Update PON progress
// @access  Private
router.put('/:id/progress', auth, async (req, res) => {
  try {
    const pon = await PON.findById(req.params.id);

    if (!pon) {
      return res.status(404).json({ message: 'PON not found' });
    }

    // Update progress based on tasks
    await pon.updateProgress();
    await pon.save();

    const updatedPON = await PON.findById(pon._id)
      .populate('projectManager', 'name email')
      .populate('siteManager', 'name email');

    res.json(updatedPON);
  } catch (error) {
    console.error(error.message);
    res.status(500).send('Server Error');
  }
});

// @route   DELETE api/pons/:id
// @desc    Delete PON
// @access  Private (Project Manager, Admin)
router.delete('/:id', [
  auth,
  authorize('project_manager', 'admin')
], async (req, res) => {
  try {
    const pon = await PON.findById(req.params.id);

    if (!pon) {
      return res.status(404).json({ message: 'PON not found' });
    }

    // Check if user owns this PON
    if (pon.projectManager.toString() !== req.user.id && req.user.role !== 'admin') {
      return res.status(403).json({ message: 'Access denied' });
    }

    // Delete associated tasks
    await Task.deleteMany({ pon: req.params.id });

    await PON.findByIdAndDelete(req.params.id);

    res.json({ message: 'PON and associated tasks deleted' });
  } catch (error) {
    console.error(error.message);
    if (error.kind === 'ObjectId') {
      return res.status(404).json({ message: 'PON not found' });
    }
    res.status(500).send('Server Error');
  }
});

module.exports = router;