const express = require('express');
const multer = require('multer');
const path = require('path');
const fs = require('fs');
const exifr = require('exifr');
const { v4: uuidv4 } = require('uuid');
const Task = require('../models/Task');
const PON = require('../models/PON');
const { auth } = require('../middleware/auth');

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

    // Parse EXIF for GPS and timestamp
    let metadata = {};
    try {
      const filePath = path.join('uploads', req.file.filename);
      const exif = await exifr.parse(filePath, { gps: true });
      if (exif) {
        metadata = {
          exifDate: exif.DateTimeOriginal || exif.CreateDate || null,
          gpsLatitude: exif.latitude || null,
          gpsLongitude: exif.longitude || null,
          gpsAccuracy: exif.GPSHPositioningError || null
        };
      }
    } catch (err) {
      // Non-fatal: keep upload but note missing EXIF
      metadata = { exifError: true };
    }

    // Validate GPS proximity to PON if available
    let gpsValid = null;
    try {
      if (metadata.gpsLatitude != null && metadata.gpsLongitude != null) {
        const pon = await PON.findById(task.pon);
        if (pon?.coordinates?.latitude != null && pon?.coordinates?.longitude != null) {
          const toRad = (v) => v * Math.PI / 180;
          const R = 6371e3;
          const dLat = toRad(metadata.gpsLatitude - pon.coordinates.latitude);
          const dLon = toRad(metadata.gpsLongitude - pon.coordinates.longitude);
          const lat1 = toRad(pon.coordinates.latitude);
          const lat2 = toRad(metadata.gpsLatitude);
          const a = Math.sin(dLat/2) * Math.sin(dLat/2) + Math.cos(lat1) * Math.cos(lat2) * Math.sin(dLon/2) * Math.sin(dLon/2);
          const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
          const distanceMeters = R * c;
          const allowedMeters = parseInt(process.env.PHOTO_GPS_RADIUS_METERS || '150', 10);
          gpsValid = distanceMeters <= allowedMeters;
          metadata.distanceMeters = Math.round(distanceMeters);
          metadata.allowedRadiusMeters = allowedMeters;
        }
      }
    } catch (err) {
      // ignore validation errors
    }

    // Add photo to task with metadata
    const photoData = {
      filename: req.file.filename,
      originalName: req.file.originalname,
      uploadedBy: req.user.id,
      uploadDate: new Date(),
      metadata,
      gpsValid
    };

    task.evidencePhotos.push(photoData);
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