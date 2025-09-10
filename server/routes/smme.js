const express = require('express');
const { auth } = require('../middleware/auth');
const PDFDocument = require('pdfkit');
const Task = require('../models/Task');

const router = express.Router();

// SMME (Small, Medium & Micro Enterprises) management module

// @route   GET api/smme
// @desc    Get SMME contractors
// @access  Private
router.get('/', auth, async (req, res) => {
  try {
    res.json({ message: 'SMME management feature - under development' });
  } catch (error) {
    console.error(error.message);
    res.status(500).send('Server Error');
  }
});

// @route   POST api/smme
// @desc    Add SMME contractor
// @access  Private
router.post('/', auth, async (req, res) => {
  try {
    res.json({ message: 'SMME contractor added - feature under development' });
  } catch (error) {
    console.error(error.message);
    res.status(500).send('Server Error');
  }
});

// @route   POST api/smme/paysheet
// @desc    Build SMME pay sheet PDF from tasks and a ratecard
// @access  Private
router.post('/paysheet', auth, async (req, res) => {
  try {
    const { smmeUserId, periodStart, periodEnd, rateCard } = req.body;
    const start = new Date(periodStart);
    const end = new Date(periodEnd);

    const tasks = await Task.find({
      assignedTo: smmeUserId,
      status: 'completed',
      completedDate: { $gte: start, $lte: end }
    }).select('title type completedDate');

    const items = tasks.map(t => {
      const rate = rateCard?.[t.type] || 0;
      return { description: `${t.title} (${t.type})`, quantity: 1, rate, amount: rate };
    });
    const total = items.reduce((s, i) => s + i.amount, 0);

    res.setHeader('Content-Type', 'application/pdf');
    res.setHeader('Content-Disposition', `attachment; filename=paysheet-${smmeUserId}-${Date.now()}.pdf`);
    const doc = new PDFDocument({ margin: 50 });
    doc.pipe(res);

    doc.fontSize(20).text('SMME Pay Sheet', { align: 'center' });
    doc.moveDown();
    doc.fontSize(12).text(`SMME User: ${smmeUserId}`);
    doc.text(`Period: ${start.toDateString()} - ${end.toDateString()}`);
    doc.moveDown();

    doc.fontSize(14).text('Items');
    items.forEach(i => {
      doc.fontSize(11).text(`${i.description}  Qty: ${i.quantity}  Rate: ${i.rate.toFixed(2)}  Amount: ${i.amount.toFixed(2)}`);
    });
    doc.moveDown();
    doc.fontSize(12).text(`Total: ${total.toFixed(2)}`, { align: 'right' });

    doc.end();
  } catch (error) {
    console.error(error.message);
    res.status(500).send('Server Error');
  }
});

module.exports = router;