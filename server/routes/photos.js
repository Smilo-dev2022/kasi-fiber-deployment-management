const express = require('express');
const multer = require('multer');
const path = require('path');
const exifr = require('exifr');
const { v4: uuidv4 } = require('uuid');
const Task = require('../models/Task');
const PON = require('../models/PON');
const Photo = require('../models/Photo');
const StateLog = require('../models/StateLog');
const { isWithinRadiusMeters } = require('../utils/geo');
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

const allowedTypes = ['image/jpeg', 'image/png', 'application/pdf'];
const fileFilter = (req, file, cb) => {
  if (allowedTypes.includes(file.mimetype)) {
    cb(null, true);
  } else {
    cb(new Error('Only JPG, PNG, or PDF files are allowed'), false);
  }
};

const upload = multer({ 
  storage: storage,
  fileFilter: fileFilter,
  limits: {
    fileSize: 10 * 1024 * 1024 // 10MB limit
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

    // Attempt to parse EXIF for images
    let exif = {};
    if (req.file.mimetype.startsWith('image/')) {
      try {
        const parsed = await exifr.parse(path.join('uploads', req.file.filename), ['GPSLatitude', 'GPSLongitude', 'DateTimeOriginal']);
        if (parsed) {
          exif = {
            gpsLatitude: parsed.GPSLatitude ?? null,
            gpsLongitude: parsed.GPSLongitude ?? null,
            dateTimeOriginal: parsed.DateTimeOriginal ? new Date(parsed.DateTimeOriginal) : null
          };
        }
      } catch (e) {
        // ignore EXIF errors
      }
    }

    // If PON has coordinates, set withinGeofence flag using 150m radius
    if (exif.gpsLatitude != null && exif.gpsLongitude != null) {
      const pon = await PON.findById(task.pon);
      if (pon?.coordinates?.latitude && pon?.coordinates?.longitude) {
        const within = isWithinRadiusMeters(
          { latitude: exif.gpsLatitude, longitude: exif.gpsLongitude },
          { latitude: pon.coordinates.latitude, longitude: pon.coordinates.longitude },
          150
        );
        exif.withinGeofence = within;
      }
    }

    // Add photo to task
    const photoData = {
      filename: req.file.filename,
      originalName: req.file.originalname,
      uploadedBy: req.user.id,
      uploadDate: new Date(),
      exif
    };

    task.evidencePhotos.push(photoData);
    await task.save();

    // Persist Photo entity and attach PON
    const ponDoc = await PON.findById(task.pon);
    const photoDoc = await Photo.create({
      task: task._id,
      filename: photoData.filename,
      originalName: photoData.originalName,
      uploadedBy: photoData.uploadedBy,
      pon: ponDoc ? ponDoc._id : undefined,
      exif: photoData.exif
    });

    await StateLog.create({ entityType: 'Photo', entityId: photoDoc._id, before: null, after: photoDoc.toObject(), actor: req.user.id });

    res.json({
      message: 'Photo uploaded successfully',
      photo: { ...photoData, id: photoDoc._id },
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