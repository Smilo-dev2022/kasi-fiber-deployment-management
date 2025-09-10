const express = require('express');
const { body, validationResult } = require('express-validator');
const { auth, authorize } = require('../middleware/auth');

const router = express.Router();

// Invoicing module

// @route   GET api/invoicing
// @desc    Get invoices
// @access  Private
router.get('/', auth, async (req, res) => {
  try {
    // TODO: Implement invoicing retrieval
    res.json({ message: 'Invoicing feature - under development' });
  } catch (error) {
    console.error(error.message);
    res.status(500).send('Server Error');
  }
});

// @route   POST api/invoicing
// @desc    Create invoice
// @access  Private
router.post('/', [
  auth,
  authorize('project_manager', 'admin'),
  body('pon', 'PON is required').isMongoId(),
  body('amount', 'Amount is required').isFloat({ min: 0 }),
  body('lines').isArray({ min: 1 })
], async (req, res) => {
  const errors = validationResult(req);
  if (!errors.isEmpty()) {
    return res.status(400).json({ errors: errors.array() });
  }
  try {
    // TODO: Implement invoice creation
    res.json({ message: 'Invoice created - feature under development' });
  } catch (error) {
    console.error(error.message);
    res.status(500).send('Server Error');
  }
});

module.exports = router;