const Task = require('../../models/Task');
const PON = require('../../models/PON');

async function scanSlaBreaches() {
  const now = new Date();
  const tasks = await Task.find({ status: { $ne: 'completed' }, dueDate: { $lt: now } });
  for (const task of tasks) {
    try {
      if (!task.breached) {
        task.breached = true;
        await task.save();
      }
      const pon = await PON.findById(task.pon);
      if (pon) {
        await pon.updateProgress();
        await pon.save();
      }
    } catch (e) {
      console.error('Failed marking breach', task._id, e);
    }
  }
}

module.exports = { scanSlaBreaches };

