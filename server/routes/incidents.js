const express = require('express');
const moment = require('moment');
const Incident = require('../models/Incident');
const PON = require('../models/PON');
const Device = require('../models/Device');
const { auth, authorize } = require('../middleware/auth');

const router = express.Router();

function computeSlaTargets(priority, openedAt = new Date()) {
  const open = moment(openedAt);
  switch (priority) {
    case 'P1':
      return { respondBy: open.clone().add(15, 'minutes').toDate(), restoreBy: open.clone().add(2, 'hours').toDate() };
    case 'P2':
      return { respondBy: open.clone().add(30, 'minutes').toDate(), restoreBy: open.clone().add(4, 'hours').toDate() };
    case 'P3':
      return { respondBy: open.clone().add(4, 'hours').toDate(), restoreBy: open.clone().add(1, 'days').toDate() };
    case 'P4':
    default:
      return { respondBy: open.clone().add(1, 'days').toDate(), restoreBy: open.clone().add(3, 'days').toDate() };
  }
}

// List incidents
router.get('/', auth, async (req, res) => {
  try {
    const { status, priority, pon, device, ward, site, q } = req.query;
    const query = {};
    if (status) query.status = status;
    if (priority) query.priority = priority;
    if (pon) query.pon = pon;
    if (device) query.device = device;
    if (ward) query.ward = ward;
    if (site) query.site = site;
    if (q) query.title = new RegExp(q, 'i');
    const incidents = await Incident.find(query).sort({ createdAt: -1 }).limit(500).populate('pon', 'ponId name').populate('device', 'name type mgmtIp');
    res.json(incidents);
  } catch (err) {
    console.error(err.message);
    res.status(500).send('Server Error');
  }
});

// Create incident
router.post('/', auth, authorize('project_manager', 'admin'), async (req, res) => {
  try {
    const { priority, openedAt } = req.body;
    const sla = computeSlaTargets(priority, openedAt ? new Date(openedAt) : new Date());
    const incident = new Incident({ ...req.body, ...sla });
    await incident.save();
    res.json(incident);
  } catch (err) {
    console.error(err.message);
    res.status(400).json({ message: 'Invalid incident payload' });
  }
});

// Update incident status/lifecycle
router.patch('/:id', auth, async (req, res) => {
  try {
    const update = { ...req.body };
    const incident = await Incident.findById(req.params.id);
    if (!incident) return res.status(404).json({ message: 'Incident not found' });

    // Transitions
    if (update.status && update.status === 'acknowledged' && !incident.acknowledgedAt) {
      incident.acknowledgedAt = new Date();
      if (incident.respondBy && incident.acknowledgedAt > incident.respondBy) {
        incident.breachedRespond = true;
      }
    }
    if (update.status && (update.status === 'resolved' || update.status === 'monitoring') && !incident.resolvedAt) {
      incident.resolvedAt = new Date();
      if (incident.restoreBy && incident.resolvedAt > incident.restoreBy) {
        incident.breachedRestore = true;
      }
    }

    // Always allow fields besides status
    delete update.respondBy;
    delete update.restoreBy;
    Object.assign(incident, update);
    await incident.save();
    res.json(incident);
  } catch (err) {
    console.error(err.message);
    res.status(400).json({ message: 'Invalid update' });
  }
});

// Close incident requires root cause and fix code and photo+GPS
router.post('/:id/close', auth, async (req, res) => {
  try {
    const { rootCause, fixCode, closureNotes, closurePhotos, closureGps } = req.body || {};
    const incident = await Incident.findById(req.params.id);
    if (!incident) return res.status(404).json({ message: 'Incident not found' });

    if (!rootCause || !fixCode) {
      return res.status(400).json({ message: 'rootCause and fixCode required' });
    }
    if (!closureGps || typeof closureGps.latitude !== 'number' || typeof closureGps.longitude !== 'number') {
      return res.status(400).json({ message: 'GPS coordinates required on closure' });
    }
    if (!closurePhotos || !Array.isArray(closurePhotos) || closurePhotos.length === 0) {
      return res.status(400).json({ message: 'At least one closure photo required' });
    }

    incident.rootCause = rootCause;
    incident.fixCode = fixCode;
    incident.closureNotes = closureNotes;
    incident.closurePhotos = closurePhotos;
    incident.closureGps = { ...closureGps, capturedAt: new Date() };
    incident.status = 'closed';
    incident.closedAt = new Date();

    await incident.save();
    res.json(incident);
  } catch (err) {
    console.error(err.message);
    res.status(400).json({ message: 'Invalid closure' });
  }
});

module.exports = router;

