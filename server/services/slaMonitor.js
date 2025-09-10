const Task = require('../models/Task');
const User = require('../models/User');
const { sendEmail } = require('../utils/email');

function shouldAlert(task) {
  const oneHour = 60 * 60 * 1000;
  if (!task.sla) return false;
  if (!task.sla.lastAlertedAt) return true;
  const elapsed = Date.now() - new Date(task.sla.lastAlertedAt).getTime();
  return elapsed > oneHour;
}

async function alertBreach(task, type) {
  try {
    const populatedTask = await Task.findById(task._id)
      .populate('assignedTo', 'name email')
      .populate('createdBy', 'name email')
      .populate('pon', 'ponId name');

    const recipients = [
      populatedTask.assignedTo?.email,
      populatedTask.createdBy?.email
    ].filter(Boolean).join(',');

    if (!recipients) return;

    const subject = `[SLA ${type.toUpperCase()} BREACH] ${populatedTask.title}`;
    const html = `
      <p>Task: <strong>${populatedTask.title}</strong></p>
      <p>PON: ${populatedTask.pon?.ponId || ''} ${populatedTask.pon?.name || ''}</p>
      <p>Type: ${populatedTask.type}</p>
      <p>Priority: ${populatedTask.priority}</p>
      <p>Status: ${populatedTask.status}</p>
      <p>Due: ${populatedTask.dueDate ? new Date(populatedTask.dueDate).toLocaleString() : 'N/A'}</p>
      <p>SLA Ack By: ${populatedTask.sla?.ackBy ? new Date(populatedTask.sla.ackBy).toLocaleString() : 'N/A'}</p>
      <p>SLA Complete By: ${populatedTask.sla?.completeBy ? new Date(populatedTask.sla.completeBy).toLocaleString() : 'N/A'}</p>
      <p>This is an automated notification.</p>
    `;

    await sendEmail({ to: recipients, subject, html, text: subject });

    task.sla.lastAlertedAt = new Date();
    await task.save();
  } catch (err) {
    console.error('alertBreach error:', err.message);
  }
}

async function checkSlaBreaches() {
  const now = new Date();

  const tasks = await Task.find({
    status: { $in: ['pending', 'in_progress', 'on_hold'] }
  });

  for (const task of tasks) {
    if (!task.sla) continue;

    // Ack breach: no ackedAt and past ackBy
    if (!task.sla.ackedAt && task.sla.ackBy && now > new Date(task.sla.ackBy)) {
      if (!task.sla.breachedAck && shouldAlert(task)) {
        await alertBreach(task, 'ack');
      }
      task.sla.breachedAck = true;
    }

    // Completion breach: not completed and past completeBy
    if (task.status !== 'completed' && task.sla.completeBy && now > new Date(task.sla.completeBy)) {
      if (!task.sla.breachedCompletion && shouldAlert(task)) {
        await alertBreach(task, 'completion');
      }
      task.sla.breachedCompletion = true;
    }

    await task.save();
  }
}

function startSlaMonitor() {
  const intervalMs = parseInt(process.env.SLA_MONITOR_INTERVAL_MS || '300000', 10); // default 5 min
  setInterval(() => {
    checkSlaBreaches().catch(err => console.error('SLA monitor error:', err.message));
  }, intervalMs);
  // Kick off immediately on startup as well
  checkSlaBreaches().catch(err => console.error('SLA monitor error:', err.message));
}

module.exports = {
  startSlaMonitor,
  checkSlaBreaches
};

