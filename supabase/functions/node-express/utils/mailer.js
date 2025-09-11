const nodemailer = require('nodemailer');

let cachedTransporter = null;

function createTransporter() {
  if (cachedTransporter) return cachedTransporter;

  const {
    SMTP_HOST,
    SMTP_PORT,
    SMTP_SECURE,
    SMTP_USER,
    SMTP_PASS
  } = process.env;

  if (SMTP_HOST && SMTP_PORT && SMTP_USER && SMTP_PASS) {
    cachedTransporter = nodemailer.createTransport({
      host: SMTP_HOST,
      port: Number(SMTP_PORT),
      secure: String(SMTP_SECURE || '').toLowerCase() === 'true',
      auth: {
        user: SMTP_USER,
        pass: SMTP_PASS
      }
    });
  } else {
    // Fallback to a JSON transport that logs emails to console
    cachedTransporter = nodemailer.createTransport({
      jsonTransport: true
    });
  }

  return cachedTransporter;
}

async function sendMail({ to, subject, text, html }) {
  const transporter = createTransporter();
  const from = process.env.MAIL_FROM || 'no-reply@kasi-fiber.local';

  const info = await transporter.sendMail({ from, to, subject, text, html });

  if (transporter.options.jsonTransport) {
    // eslint-disable-next-line no-console
    console.log('Mail (jsonTransport):', JSON.stringify({ to, subject, text }, null, 2));
  }

  return info;
}

module.exports = { sendMail };

