const express = require('express');
const { auth } = require('../middleware/auth');
const PDFDocument = require('pdfkit');

const router = express.Router();

// Invoicing module

// @route   GET api/invoicing
// @desc    Get invoices
// @access  Private
router.get('/', auth, async (req, res) => {
  try {
    res.json({ message: 'Invoicing feature - under development' });
  } catch (error) {
    console.error(error.message);
    res.status(500).send('Server Error');
  }
});

// @route   POST api/invoicing
// @desc    Create invoice
// @access  Private
router.post('/', auth, async (req, res) => {
  try {
    const { contractorName, periodStart, periodEnd, lineItems, rateCardName } = req.body;
    const doc = new PDFDocument({ margin: 50 });
    res.setHeader('Content-Type', 'application/pdf');
    res.setHeader('Content-Disposition', `attachment; filename=invoice-${Date.now()}.pdf`);
    doc.pipe(res);

    doc.fontSize(20).text('SMME Pay Sheet / Invoice', { align: 'center' });
    doc.moveDown();
    doc.fontSize(12).text(`Contractor: ${contractorName || 'N/A'}`);
    doc.text(`Period: ${periodStart || ''} - ${periodEnd || ''}`);
    doc.text(`Rate Card: ${rateCardName || 'Standard'}`);
    doc.moveDown();

    doc.fontSize(14).text('Line Items');
    doc.moveDown(0.3);
    let total = 0;
    (lineItems || []).forEach((item) => {
      const qty = Number(item.quantity || 0);
      const rate = Number(item.rate || 0);
      const amount = qty * rate;
      total += amount;
      doc.fontSize(11).text(`${item.description || ''}  Qty: ${qty}  Rate: ${rate.toFixed(2)}  Amount: ${amount.toFixed(2)}`);
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