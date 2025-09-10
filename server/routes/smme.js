const express = require('express');
const { body, validationResult } = require('express-validator');
const { auth, authorize } = require('../middleware/auth');

const router = express.Router();

// SMME (Small, Medium & Micro Enterprises) management module

// @route   GET api/smme
// @desc    Get SMME contractors
// @access  Private
router.get('/', auth, async (req, res) => {
  try {
    // TODO: Implement SMME contractors retrieval
    res.json({ message: 'SMME management feature - under development' });
  } catch (error) {
    console.error(error.message);
    res.status(500).send('Server Error');
  }
});

// @route   POST api/smme
// @desc    Add SMME contractor
// @access  Private
router.post('/', [auth, authorize('project_manager', 'admin'), body('name').isString().notEmpty()], async (req, res) => {
  try {
    const errors = validationResult(req);
    if (!errors.isEmpty()) return res.status(400).json({ errors: errors.array() });
    // TODO: Implement SMME contractor addition
    res.json({ message: 'SMME contractor added - feature under development' });
  } catch (error) {
    console.error(error.message);
    res.status(500).send('Server Error');
  }
});

module.exports = router;