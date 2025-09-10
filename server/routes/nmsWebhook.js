const express = require('express');
const Incident = require('../models/Incident');
const Device = require('../models/Device');
const PON = require('../models/PON');

const router = express.Router();

// No auth: called by NMS in network. Secure via shared secret header and per-IP rate limit
router.post('/hook', async (req, res) => {
  try {
    // Simple per-IP sliding window limiter using memory map (OK for single instance)
    const now = Date.now();
    const ip = (req.headers['x-forwarded-for'] || req.socket.remoteAddress || 'unknown').toString().split(',')[0].trim();
    const limit = Number(process.env.WEBHOOK_IP_LIMIT || 60);
    const windowSec = Number(process.env.WEBHOOK_IP_WINDOW || 60);
    const key = `ip:${ip}`;
    if (!global.__ipBuckets) global.__ipBuckets = new Map();
    const arr = (global.__ipBuckets.get(key) || []).filter(ts => ts > now - windowSec * 1000);
    if (arr.length >= limit) {
      return res.status(429).json({ message: 'Rate limit exceeded' });
    }
    arr.push(now);
    global.__ipBuckets.set(key, arr);

    const secret = process.env.NMS_WEBHOOK_SECRET || 'change-me';
    const provided = req.header('x-webhook-secret');
    if (!provided || provided !== secret) {
      return res.status(401).json({ message: 'Unauthorized' });
    }

    const body = req.body || {};
    // Support LibreNMS and Zabbix minimal payload mapping
    const source = body.source || body.nms || (body.alert ? 'Zabbix' : 'LibreNMS');
    const eventId = body.event_id || body.alertid || body.id || `${Date.now()}-${Math.random()}`;
    const category = body.category || body.rule || body.trigger || 'other';
    const severity = (body.severity || body.priority || '').toString().toUpperCase();

    // Device correlation by IP or serial
    const mgmtIp = body.ip || body.mgmt_ip || (body.device && body.device.ip);
    const serial = body.serial || (body.device && body.device.serial);
    let device = null;
    if (mgmtIp) device = await Device.findOne({ mgmtIp });
    if (!device && serial) device = await Device.findOne({ serial });

    // PON correlation by provided id or device reference
    let pon = null;
    const ponId = body.pon || body.pon_id || null;
    if (ponId) {
      try { pon = await PON.findById(ponId); } catch (e) { /* ignore */ }
    }
    if (!pon && device && device.pon) {
      pon = await PON.findById(device.pon);
    }

    // Map to Incident priority based on alerts
    let priority = 'P3';
    const lower = (body.alert || body.event || category || '').toString().toLowerCase();
    if (lower.includes('device down') || lower.includes('core') || lower.includes('uplink down')) priority = 'P1';
    else if (lower.includes('los') || lower.includes('olt card down')) priority = 'P1';
    else if (lower.includes('area') || lower.includes('power loss')) priority = 'P2';
    else if (lower.includes('optical') || lower.includes('low power')) priority = 'P2';

    const title = body.title || body.host || body.device_name || `${category} on ${device?.name || mgmtIp || 'unknown'}`;
    const openedAt = body.timestamp ? new Date(body.timestamp * 1000) : new Date();

    // Upsert (reopen if exists)
    const existing = await Incident.findOne({ nmsSource: source, nmsEventId: String(eventId), status: { $in: ['open', 'acknowledged', 'in_progress', 'monitoring'] } });
    if (existing) {
      // Update signals context
      existing.signals.push({ key: 'update', value: JSON.stringify(body).slice(0, 2000) });
      await existing.save();
      return res.json({ ok: true, incidentId: existing._id, status: existing.status, updated: true });
    }

    const incident = new Incident({
      title,
      description: body.message || body.alert_message || '',
      priority,
      category: mapCategory(lower),
      tenant: body.tenant || undefined,
      ward: body.ward || undefined,
      site: body.site || undefined,
      pon: pon ? pon._id : undefined,
      device: device ? device._id : undefined,
      relatedOnuId: body.onu || body.onu_id || undefined,
      nmsSource: source,
      nmsEventId: String(eventId),
      openedAt,
      signals: [
        { key: 'raw', value: JSON.stringify(body).slice(0, 2000) }
      ]
    });
    // Compute SLA times
    const { respondBy, restoreBy } = computeSlaTargets(priority, openedAt);
    incident.respondBy = respondBy;
    incident.restoreBy = restoreBy;
    await incident.save();

    res.json({ ok: true, incidentId: incident._id });
  } catch (err) {
    console.error(err.message);
    res.status(400).json({ message: 'Invalid webhook' });
  }
});

function computeSlaTargets(priority, openedAt) {
  const d = new Date(openedAt || Date.now());
  const addMinutes = (minutes) => new Date(d.getTime() + minutes * 60 * 1000);
  switch (priority) {
    case 'P1': return { respondBy: addMinutes(15), restoreBy: addMinutes(120) };
    case 'P2': return { respondBy: addMinutes(30), restoreBy: addMinutes(240) };
    case 'P3': return { respondBy: addMinutes(240), restoreBy: addMinutes(1440) };
    default: return { respondBy: addMinutes(1440), restoreBy: addMinutes(4320) };
  }
}

function mapCategory(lower) {
  if (lower.includes('los') || lower.includes('lof') || lower.includes('lop')) return 'los';
  if (lower.includes('device down')) return 'device_down';
  if (lower.includes('uplink down')) return 'uplink_down';
  if (lower.includes('low power') || lower.includes('optical')) return 'optical_low_power';
  if (lower.includes('flap')) return 'interface_flaps';
  if (lower.includes('cpu')) return 'high_cpu';
  if (lower.includes('power loss')) return 'power_loss';
  if (lower.includes('config')) return 'config_drift';
  return 'other';
}

module.exports = router;

