const moment = require('moment');
const Task = require('../models/Task');
const User = require('../models/User');
const { sendMail } = require('../utils/mailer');

const DEFAULT_INTERVAL_MS = 60 * 1000; // 1 minute

function buildWarningEmail({ task, assignee, creator }) {
  const subject = `[SLA Warning] Task ${task.title} due soon`;
  const due = moment(task.sla?.targetAt || task.dueDate).format('YYYY-MM-DD HH:mm');
  const text = `Task "${task.title}" is approaching its SLA.
Status: ${task.status}
Due: ${due}
PON: ${task.pon?.ponId || ''} ${task.pon?.name || ''}
`;
  return { subject, text };
}

function buildBreachEmail({ task, assignee, creator }) {
  const subject = `[SLA Breached] Task ${task.title} overdue`;
  const due = moment(task.sla?.targetAt || task.dueDate).format('YYYY-MM-DD HH:mm');
  const text = `Task "${task.title}" has BREACHED its SLA.
Status: ${task.status}
Due: ${due}
PON: ${task.pon?.ponId || ''} ${task.pon?.name || ''}
`;
  return { subject, text };
}

async function runSlaCheckOnce(now = new Date()) {
  const nowMoment = moment(now);

  const tasks = await Task.find({
    'sla.enabled': { $ne: false },
    status: { $in: ['pending', 'in_progress', 'on_hold'] },
    dueDate: { $ne: null }
  })
    .populate('assignedTo', 'name email')
    .populate('createdBy', 'name email')
    .populate('pon', 'ponId name');

  const emailPromises = [];

  for (const task of tasks) {
    const targetAt = task.sla?.targetAt || task.dueDate;
    if (!targetAt) continue;

    const warnBeforeMinutes = typeof task.sla?.warnBeforeMinutes === 'number' ? task.sla.warnBeforeMinutes : 60;
    const warnAt = moment(targetAt).subtract(warnBeforeMinutes, 'minutes');

    // Warning
    if (!task.sla?.warningNotifiedAt && nowMoment.isSameOrAfter(warnAt) && nowMoment.isBefore(targetAt)) {
      const { subject, text } = buildWarningEmail({ task });
      const to = [task.assignedTo?.email, task.createdBy?.email].filter(Boolean).join(',');
      if (to) {
        emailPromises.push(sendMail({ to, subject, text }));
      }
      task.sla.warningNotifiedAt = new Date();
      await task.save();
    }

    // Breach
    if (!task.sla?.breachNotifiedAt && nowMoment.isAfter(targetAt)) {
      const { subject, text } = buildBreachEmail({ task });
      const to = [task.assignedTo?.email, task.createdBy?.email].filter(Boolean).join(',');
      if (to) {
        emailPromises.push(sendMail({ to, subject, text }));
      }
      task.sla.breachNotifiedAt = new Date();
      await task.save();
    }
  }

  await Promise.allSettled(emailPromises);
}

function startSlaMonitor(intervalMs = DEFAULT_INTERVAL_MS) {
  // eslint-disable-next-line no-console
  console.log(`[SLA Monitor] Starting with interval ${intervalMs}ms`);
  const timer = setInterval(() => {
    runSlaCheckOnce().catch((err) => console.error('[SLA Monitor] Error:', err));
  }, intervalMs);
  return () => clearInterval(timer);
}

module.exports = { startSlaMonitor, runSlaCheckOnce };

