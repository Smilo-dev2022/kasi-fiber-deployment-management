const cron = require('node-cron');

let tasks = [];

function start() {
  // SLA breach scan every 15 minutes
  const slaTask = cron.schedule('*/15 * * * *', async () => {
    try {
      const { scanSlaBreaches } = require('./tasks/sla');
      await scanSlaBreaches();
    } catch (e) {
      console.error('SLA scan failed:', e);
    }
  }, { scheduled: true });

  // Photo revalidation daily 18:00 SAST (Africa/Johannesburg)
  const photoTask = cron.schedule('0 18 * * *', async () => {
    try {
      const { revalidatePhotos } = require('./tasks/photos');
      await revalidatePhotos();
    } catch (e) {
      console.error('Photo revalidation failed:', e);
    }
  }, { scheduled: true, timezone: 'Africa/Johannesburg' });

  // Weekly report Monday 06:00 SAST
  const weeklyTask = cron.schedule('0 6 * * 1', async () => {
    try {
      const { sendWeeklyReport } = require('./tasks/reports');
      await sendWeeklyReport();
    } catch (e) {
      console.error('Weekly report failed:', e);
    }
  }, { scheduled: true, timezone: 'Africa/Johannesburg' });

  tasks = [slaTask, photoTask, weeklyTask];
}

function stop() {
  tasks.forEach(t => t.stop());
  tasks = [];
}

module.exports = { start, stop };

