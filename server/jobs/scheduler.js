const cron = require('node-cron');
const Task = require('../models/Task');
const PON = require('../models/PON');
const Photo = require('../models/Photo');

function registerJobs() {
  // SLA breach scan every 15 minutes
  cron.schedule('*/15 * * * *', async () => {
    const now = new Date();
    const tasks = await Task.find({ status: { $ne: 'completed' }, dueDate: { $lt: now } });
    for (const t of tasks) {
      if (!t.breached) {
        t.breached = true;
        await t.save();
        const pon = await PON.findById(t.pon);
        if (pon) { await pon.updateProgress(); await pon.save(); }
      }
    }
    // eslint-disable-next-line no-console
    console.log(JSON.stringify({ level: 'info', ts: new Date().toISOString(), job: 'sla_breach_scan', updated: tasks.length }));
  });

  // Photo revalidation daily 18:00
  cron.schedule('0 18 * * *', async () => {
    const photos = await Photo.find({ 'exif.gps': { $ne: null } }).limit(1000);
    // Placeholder for advanced validations
    // eslint-disable-next-line no-console
    console.log(JSON.stringify({ level: 'info', ts: new Date().toISOString(), job: 'photo_revalidation', checked: photos.length }));
  });

  // Weekly report Monday 06:00 SAST (UTC+2). Using UTC cron 04:00.
  cron.schedule('0 4 * * 1', async () => {
    // Placeholder: gather stats and email
    // eslint-disable-next-line no-console
    console.log(JSON.stringify({ level: 'info', ts: new Date().toISOString(), job: 'weekly_report_generated' }));
  });
}

module.exports = { registerJobs };

