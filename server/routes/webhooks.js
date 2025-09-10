const express = require('express');
const crypto = require('crypto');
const rateLimit = require('express-rate-limit');
const ipaddr = require('ipaddr.js');

const router = express.Router();
const Incident = require('../models/Incident');
const Device = require('../models/Device');
const OpticalReading = require('../models/OpticalReading');
const MaintenanceWindow = require('../models/MaintenanceWindow');

// Rate limiting for webhook endpoints
const webhookLimiter = rateLimit({
  windowMs: Number(process.env.WEBHOOK_RATE_LIMIT_WINDOW_MS || 60_000),
  max: Number(process.env.WEBHOOK_RATE_LIMIT_MAX || 300),
  standardHeaders: true,
  legacyHeaders: false,
  keyGenerator: (req) => req.ip,
});

function parseWhitelist() {
  const list = (process.env.NMS_IP_WHITELIST || '').split(',').map(s => s.trim()).filter(Boolean);
  const cidrs = [];
  for (const entry of list) {
    try {
      if (entry.includes('/')) {
        cidrs.push(ipaddr.parseCIDR(entry));
      } else {
        // Single IP -> convert to host-specific CIDR
        const parsed = ipaddr.parse(entry);
        if (parsed.kind() === 'ipv6') {
          cidrs.push([parsed, 128]);
        } else {
          cidrs.push([parsed, 32]);
        }
      }
    } catch (_) {
      // Skip invalid entries
    }
  }
  return cidrs;
}

const WHITELIST_CIDRS = parseWhitelist();

function isIpAllowed(ip) {
  if (process.env.NMS_IP_WHITELIST_OPTIONAL === 'true') return true;
  if (WHITELIST_CIDRS.length === 0) return false;
  try {
    const addr = ipaddr.process(ip);
    return WHITELIST_CIDRS.some(([net, prefix]) => addr.match([net, prefix]));
  } catch (_) {
    return false;
  }
}

function constantTimeEqual(a, b) {
  const bufA = Buffer.from(a);
  const bufB = Buffer.from(b);
  if (bufA.length !== bufB.length) return false;
  return crypto.timingSafeEqual(bufA, bufB);
}

function pickSignatureHeader(req, vendor) {
  const candidates = [
    'x-webhook-signature',
    'x-hub-signature-256',
    vendor === 'librenms' ? 'x-librenms-signature' : null,
    vendor === 'zabbix' ? 'x-zabbix-signature' : null,
  ].filter(Boolean);
  for (const h of candidates) {
    const v = req.header(h);
    if (v) return { header: h, value: v };
  }
  return null;
}

function getSecretForVendor(vendor) {
  if (vendor === 'librenms') return process.env.WEBHOOK_SECRET_LIBRENMS || '';
  if (vendor === 'zabbix') return process.env.WEBHOOK_SECRET_ZABBIX || '';
  return process.env.WEBHOOK_SECRET_GENERIC || '';
}

function verifyHmac(req, vendor) {
  const secret = getSecretForVendor(vendor);
  const optional = process.env.WEBHOOK_HMAC_OPTIONAL === 'true';
  if (!secret) return optional;

  const sig = pickSignatureHeader(req, vendor);
  if (!sig) return false;

  const timestamp = req.header('x-webhook-timestamp');
  const requireTs = process.env.WEBHOOK_REQUIRE_TIMESTAMP === 'true';
  const maxSkewSec = Number(process.env.WEBHOOK_MAX_SKEW_SEC || 300);
  let signedPayload;
  if (timestamp) {
    const ts = Number(timestamp);
    if (!Number.isFinite(ts)) return false;
    const skew = Math.abs(Date.now() - ts);
    if (requireTs && skew > maxSkewSec * 1000) return false;
    signedPayload = `${timestamp}.${req.rawBody?.toString('utf8') || ''}`;
  } else {
    if (requireTs) return false;
    signedPayload = req.rawBody?.toString('utf8') || '';
  }

  const computed = crypto.createHmac('sha256', secret).update(signedPayload).digest('hex');
  let provided = sig.value.trim();
  if (sig.header.toLowerCase() === 'x-hub-signature-256' && provided.startsWith('sha256=')) {
    provided = provided.slice('sha256='.length);
  }
  return constantTimeEqual(computed, provided);
}

function ensureGuards(vendor) {
  return [
    webhookLimiter,
    (req, res, next) => {
      const clientIp = req.ip;
      if (!isIpAllowed(clientIp)) {
        return res.status(403).json({ message: 'Source IP not allowed' });
      }
      next();
    },
    (req, res, next) => {
      if (!verifyHmac(req, vendor)) {
        return res.status(401).json({ message: 'Invalid signature' });
      }
      next();
    }
  ];
}

function normalizeEvent(vendor, body) {
  let hostname = body.hostname || body.host || body.device || body.sysName || body.device_name;
  let severity = (body.severity || body.priority || body.level || '').toString().toLowerCase();
  let status = (body.status || body.state || body.event || '').toString().toLowerCase();
  let message = body.message || body.alert || body.trigger || body.summary || '';

  // Derive eventType
  const text = `${severity} ${status} ${message}`;
  let eventType = 'unknown';
  if (/optical/.test(text) && /(low|los|lofl|power)/.test(text)) {
    eventType = 'optical_low';
  } else if (/(clear|ok|recovered|resolved|up)/.test(text)) {
    eventType = 'clear';
  } else if (/(down|problem|disconnected|unreachable)/.test(text)) {
    eventType = 'down';
  } else if (/(up|available|connected)/.test(text)) {
    eventType = 'up';
  }

  return {
    vendor,
    deviceHostname: hostname,
    severity,
    status,
    eventType,
    message,
    receivedAt: new Date().toISOString(),
    raw: body,
  };
}

function mapSeverityToP(severity, eventType) {
  const s = (severity || '').toLowerCase();
  if (eventType === 'down') return 'p1';
  if (eventType === 'optical_low') return 'p2';
  if (s.includes('critical') || s === '5') return 'p1';
  if (s.includes('high') || s === '4') return 'p2';
  if (s.includes('medium') || s === '3') return 'p3';
  return 'p4';
}

function buildDedupKey(payload) {
  return [payload.vendor, payload.deviceHostname || 'unknown', payload.eventType || 'unknown'].join('|');
}

async function openOrUpdateIncident(device, payload) {
  // Suppress during approved maintenance windows
  const now = new Date();
  const inMw = await MaintenanceWindow.findOne({
    approved: true,
    startAt: { $lte: now },
    endAt: { $gte: now },
    $or: [
      { deviceHostnames: payload.deviceHostname?.toLowerCase() },
      { wards: device?.ward },
      { ponIds: device?.ponId },
    ]
  });
  if (inMw) {
    return null; // suppressed
  }
  const dedupKey = buildDedupKey(payload);
  const severity = mapSeverityToP(payload.severity, payload.eventType);
  
  let inc = await Incident.findOne({ dedupKey, status: { $in: ['open', 'ack'] } });
  if (!inc && payload.eventType !== 'clear' && payload.eventType !== 'up') {
    inc = new Incident({
      device: device?._id,
      deviceHostname: payload.deviceHostname?.toLowerCase(),
      eventType: payload.eventType,
      severity,
      status: 'open',
      message: payload.message,
      dedupKey,
      openedAt: now,
      vendor: payload.vendor,
      raw: payload.raw,
      ward: device?.ward,
      ponId: device?.ponId,
    });
    await inc.save();
  }
  return inc;
}

async function resolveIncidentIfAny(payload) {
  const dedupKey = buildDedupKey({ ...payload, eventType: payload.eventType === 'clear' ? 'down' : payload.eventType });
  const now = new Date();
  const inc = await Incident.findOne({ dedupKey, status: { $in: ['open', 'ack'] } });
  if (inc) {
    inc.status = 'resolved';
    inc.resolvedAt = now;
    if (inc.openedAt) inc.mttrMs = now.getTime() - inc.openedAt.getTime();
    await inc.save();
  }
  return inc;
}

// Helper: map NMS hostname to app Device, upsert if unknown
async function resolveDevice(hostname, metadata) {
  const Device = require('../models/Device');
  if (!hostname) return null;
  const normalized = hostname.toString().trim().toLowerCase();
  let device = await Device.findOne({ hostname: normalized });
  if (!device) {
    device = new Device({ hostname: normalized, name: metadata?.name || hostname, vendor: 'unknown', metadata });
  } else if (metadata && typeof metadata === 'object') {
    device.metadata = { ...(device.metadata || {}), ...metadata };
  }
  device.lastSeenAt = new Date();
  await device.save();
  return device;
}

// LibreNMS webhook endpoint
router.post('/librenms', ensureGuards('librenms'), async (req, res) => {
  try {
    const body = req.body || {};
    const payload = normalizeEvent('librenms', body);
    const device = await resolveDevice(payload.deviceHostname, { vendor: 'librenms', source: 'webhook' });
    if (payload.eventType === 'clear' || payload.eventType === 'up') {
      await resolveIncidentIfAny(payload);
    } else {
      await openOrUpdateIncident(device, payload);
    }
    // Handle optical readings if present
    if (body.optical_power_dbm != null) {
      const reading = new OpticalReading({
        device: device?._id,
        deviceHostname: payload.deviceHostname?.toLowerCase(),
        port: body.port || body.ifName || body.interface,
        onuId: body.onu || body.onu_id || body.onuId,
        direction: body.direction === 'tx' ? 'tx' : 'rx',
        powerDbm: Number(body.optical_power_dbm),
        takenAt: new Date(body.timestamp || Date.now()),
        source: 'nms',
        ward: device?.ward,
        ponId: device?.ponId,
        metadata: { vendor: 'librenms' }
      });
      await reading.save();
    }
    console.log('[Webhook][LibreNMS] accepted', { device: device?.hostname, eventType: payload.eventType });
    return res.status(202).json({ accepted: true });
  } catch (err) {
    console.error('LibreNMS webhook error:', err);
    return res.status(500).json({ message: 'Server error' });
  }
});

// Zabbix webhook endpoint
router.post('/zabbix', ensureGuards('zabbix'), async (req, res) => {
  try {
    const body = req.body || {};
    const payload = normalizeEvent('zabbix', body);
    const device = await resolveDevice(payload.deviceHostname, { vendor: 'zabbix', source: 'webhook' });
    if (payload.eventType === 'clear' || payload.eventType === 'up') {
      await resolveIncidentIfAny(payload);
    } else {
      await openOrUpdateIncident(device, payload);
    }
    // Zabbix optical value fields may vary
    const optical = body.optical_power_dbm || body.rx_power_dbm || body.tx_power_dbm;
    if (optical != null) {
      const reading = new OpticalReading({
        device: device?._id,
        deviceHostname: payload.deviceHostname?.toLowerCase(),
        port: body.port || body.interface || body.ifName,
        onuId: body.onu || body.onu_id || body.onuId,
        direction: body.tx_power_dbm != null ? 'tx' : 'rx',
        powerDbm: Number(optical),
        takenAt: new Date(body.timestamp || Date.now()),
        source: 'nms',
        ward: device?.ward,
        ponId: device?.ponId,
        metadata: { vendor: 'zabbix' }
      });
      await reading.save();
    }
    console.log('[Webhook][Zabbix] accepted', { device: device?.hostname, eventType: payload.eventType });
    return res.status(202).json({ accepted: true });
  } catch (err) {
    console.error('Zabbix webhook error:', err);
    return res.status(500).json({ message: 'Server error' });
  }
});

// Test endpoint to simulate events during setup
router.post('/test', webhookLimiter, (req, res) => {
  const { vendor = 'test', hostname = 'test-device-1', eventType = 'down', severity = 'critical', message = 'Test event' } = req.body || {};
  const payload = {
    vendor,
    deviceHostname: hostname,
    severity,
    status: eventType,
    eventType,
    message,
    receivedAt: new Date().toISOString(),
  };
  console.log('[Webhook][Test]', payload);
  return res.status(202).json({ accepted: true });
});

module.exports = router;

