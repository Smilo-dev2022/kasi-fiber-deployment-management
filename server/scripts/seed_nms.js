/* eslint-disable no-console */
require('dotenv').config();
const mongoose = require('mongoose');
const connectDB = require('../config/database');
const Device = require('../models/Device');
const OpticalReading = require('../models/OpticalReading');

async function run() {
  await connectDB();
  const now = new Date();
  const devices = [
    { hostname: 'olt-ward1-a', name: 'OLT A', ward: 'Ward 1', ponId: 'PON-001', ipAddress: '10.0.1.10', vendor: 'unknown', status: 'up', lastSeenAt: now },
    { hostname: 'olt-ward1-b', name: 'OLT B', ward: 'Ward 1', ponId: 'PON-002', ipAddress: '10.0.1.11', vendor: 'unknown', status: 'up', lastSeenAt: now },
    { hostname: 'onu-ward1-101', name: 'ONU 101', ward: 'Ward 1', ponId: 'PON-001', ipAddress: '10.0.1.101', vendor: 'unknown', status: 'up', lastSeenAt: now },
  ];
  for (const d of devices) {
    const existing = await Device.findOne({ hostname: d.hostname });
    if (existing) {
      Object.assign(existing, d);
      await existing.save();
    } else {
      await new Device(d).save();
    }
  }

  const baseline = [
    { deviceHostname: 'onu-ward1-101', port: 'gpon0/1', onuId: '101', direction: 'rx', powerDbm: -22.5, baselineDbm: -22.0, takenAt: now, source: 'seed' },
    { deviceHostname: 'olt-ward1-a', port: 'pon0/1', onuId: '101', direction: 'tx', powerDbm: 2.0, baselineDbm: 2.5, takenAt: now, source: 'seed' },
  ];
  for (const r of baseline) {
    const device = await Device.findOne({ hostname: r.deviceHostname });
    await new OpticalReading({ ...r, device: device?._id, ward: device?.ward, ponId: device?.ponId }).save();
  }

  console.log('Seed complete');
  await mongoose.connection.close();
}

run().catch(async (e) => {
  console.error(e);
  try { await mongoose.connection.close(); } catch (_) {}
  process.exit(1);
});

