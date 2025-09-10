const nodemailer = require('nodemailer');

let cachedTransporter = null;

function getTransporter() {
  if (cachedTransporter) return cachedTransporter;

  const host = process.env.SMTP_HOST || 'localhost';
  const port = parseInt(process.env.SMTP_PORT || '1025', 10);
  const secure = process.env.SMTP_SECURE === 'true';

  cachedTransporter = nodemailer.createTransport({
    host,
    port,
    secure,
    auth: process.env.SMTP_USER && process.env.SMTP_PASS ? {
      user: process.env.SMTP_USER,
      pass: process.env.SMTP_PASS
    } : undefined
  });

  return cachedTransporter;
}

async function sendEmail({ to, subject, html, text }) {
  const from = process.env.EMAIL_FROM || 'no-reply@kasi-fiber.local';
  const transporter = getTransporter();
  try {
    await transporter.sendMail({ from, to, subject, html, text });
  } catch (err) {
    console.error('Email send failed:', err.message);
  }
}

module.exports = {
  sendEmail
};

