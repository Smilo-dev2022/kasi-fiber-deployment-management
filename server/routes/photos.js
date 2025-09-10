const express = require('express');
const multer = require('multer');
const path = require('path');
const { v4: uuidv4 } = require('uuid');
const Task = require('../models/Task');
const PON = require('../models/PON');
const { auth } = require('../middleware/auth');
const exifr = require('exifr');
const fs = require('fs');

const router = express.Router();

// Configure multer for photo uploads
const storage = multer.diskStorage({
  destination: function (req, file, cb) {
    cb(null, 'uploads/');
  },
  filename: function (req, file, cb) {
    const uniqueName = uuidv4() + path.extname(file.originalname);
    cb(null, uniqueName);
  }
});

const fileFilter = (req, file, cb) => {
  // Accept images only
  if (file.mimetype.startsWith('image/')) {
    cb(null, true);
  } else {
    cb(new Error('Only image files are allowed'), false);
  }
};

const upload = multer({ 
  storage: storage,
  fileFilter: fileFilter,
  limits: {
    fileSize: 5 * 1024 * 1024 // 5MB limit
  }
});

// @route   POST api/photos/upload/:taskId
// @desc    Upload photo evidence for a task
// @access  Private
router.post('/upload/:taskId', auth, upload.single('photo'), async (req, res) => {
  try {
    const task = await Task.findById(req.params.taskId);
    
    if (!task) {
      return res.status(404).json({ message: 'Task not found' });
    }

    // Check if user can upload evidence for this task
    if (task.assignedTo.toString() !== req.user.id && 
        task.createdBy.toString() !== req.user.id && 
        req.user.role !== 'admin') {
      return res.status(403).json({ message: 'Access denied' });
    }

    if (!req.file) {
      return res.status(400).json({ message: 'No file uploaded' });
    }

    // Extract EXIF and GPS
    let exifData = null;
    let gpsData = null;
    let validationErrors = [];
    let timeValid = false;
    let geofenceValid = false;

    try {
      exifData = await exifr.parse(req.file.path, { gps: true });
      if (exifData) {
        gpsData = {
          latitude: exifData.latitude,
          longitude: exifData.longitude,
          altitude: typeof exifData.altitude === 'number' ? exifData.altitude : undefined,
          accuracyMeters: undefined
        };
      }
    } catch (e) {
      validationErrors.push('Failed to read EXIF');
    }

    const exifPresent = Boolean(exifData && (exifData.latitude != null && exifData.longitude != null));

    if (!exifPresent) {
      // Clean up file to prevent orphaned invalid uploads
      try { fs.unlinkSync(req.file.path); } catch (_) {}
      return res.status(400).json({ message: 'EXIF GPS data missing. Enable location in camera.' });
    }

    // Validate time difference
    const maxAgeMinutes = parseInt(process.env.EXIF_MAX_AGE_MINUTES || '360', 10); // default 6 hours
    const exifTime = exifData.DateTimeOriginal || exifData.CreateDate || exifData.ModifyDate;
    const exifDate = exifTime ? new Date(exifTime) : null;
    if (exifDate) {
      const diffMinutes = Math.abs((Date.now() - exifDate.getTime()) / 60000);
      timeValid = diffMinutes <= maxAgeMinutes;
      if (!timeValid) {
        validationErrors.push('Photo timestamp too far from current time');
      }
    } else {
      validationErrors.push('EXIF timestamp missing');
    }

    // Validate geofence
    const pon = await PON.findById(task.pon);
    if (!pon) {
      try { fs.unlinkSync(req.file.path); } catch (_) {}
      return res.status(404).json({ message: 'Associated PON not found' });
    }

    const centerLat = (pon.geofence && pon.geofence.center && pon.geofence.center.latitude != null)
      ? pon.geofence.center.latitude
      : (pon.coordinates ? pon.coordinates.latitude : null);
    const centerLng = (pon.geofence && pon.geofence.center && pon.geofence.center.longitude != null)
      ? pon.geofence.center.longitude
      : (pon.coordinates ? pon.coordinates.longitude : null);
    const radiusMeters = (pon.geofence && pon.geofence.radiusMeters) || parseInt(process.env.GEOFENCE_DEFAULT_RADIUS_METERS || '300', 10);

    if (centerLat == null || centerLng == null) {
      validationErrors.push('PON geofence center missing');
    } else {
      const distanceMeters = haversineDistanceMeters(centerLat, centerLng, gpsData.latitude, gpsData.longitude);
      geofenceValid = distanceMeters <= radiusMeters;
      if (!geofenceValid) {
        validationErrors.push('Photo outside PON geofence');
      }
    }

    if (!timeValid || !geofenceValid) {
      try { fs.unlinkSync(req.file.path); } catch (_) {}
      return res.status(400).json({ message: 'Photo failed validation', errors: validationErrors });
    }

    // Add photo to task with validation data
    const photoData = {
      filename: req.file.filename,
      originalName: req.file.originalname,
      uploadedBy: req.user.id,
      uploadDate: new Date(),
      exif: {
        make: exifData.Make,
        model: exifData.Model,
        datetimeOriginal: exifDate || undefined
      },
      gps: gpsData,
      validations: {
        exifPresent,
        timeValid,
        geofenceValid,
        errors: validationErrors
      }
    };

    task.evidencePhotos.push(photoData);
    task.lastPhotoGps = { latitude: gpsData.latitude, longitude: gpsData.longitude, timestamp: exifDate || new Date() };
    await task.save();

    res.json({
      message: 'Photo uploaded successfully',
      photo: photoData,
      url: `/uploads/${req.file.filename}`
    });
  } catch (error) {
    console.error(error.message);
    res.status(500).send('Server Error');
  }
});

// @route   GET api/photos/task/:taskId
// @desc    Get photos for a task
// @access  Private
router.get('/task/:taskId', auth, async (req, res) => {
  try {
    const task = await Task.findById(req.params.taskId)
      .populate('evidencePhotos.uploadedBy', 'name email');
    
    if (!task) {
      return res.status(404).json({ message: 'Task not found' });
    }

    const photosWithUrls = task.evidencePhotos.map(photo => ({
      ...photo.toObject(),
      url: `/uploads/${photo.filename}`
    }));

    res.json(photosWithUrls);
  } catch (error) {
    console.error(error.message);
    res.status(500).send('Server Error');
  }
});

module.exports = router;

// Utilities
function haversineDistanceMeters(lat1, lon1, lat2, lon2) {
  const toRad = (deg) => (deg * Math.PI) / 180;
  const R = 6371000; // meters
  const dLat = toRad(lat2 - lat1);
  const dLon = toRad(lon2 - lon1);
  const a = Math.sin(dLat / 2) * Math.sin(dLat / 2) +
    Math.cos(toRad(lat1)) * Math.cos(toRad(lat2)) *
    Math.sin(dLon / 2) * Math.sin(dLon / 2);
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
  return R * c;
}