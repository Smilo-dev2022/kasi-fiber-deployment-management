const express = require('express');
const fs = require('fs');
const multer = require('multer');
const path = require('path');
const { v4: uuidv4 } = require('uuid');
const Task = require('../models/Task');
const PON = require('../models/PON');
const Photo = require('../models/Photo');
const { parseExifFromFile, isWithinGeofence } = require('../utils/exif');
const { auth } = require('../middleware/auth');

const router = express.Router();

// Ensure uploads directory exists
const uploadsDir = path.join(process.cwd(), 'uploads');
if (!fs.existsSync(uploadsDir)) {
  fs.mkdirSync(uploadsDir, { recursive: true });
}

// Configure multer for photo uploads
const storage = multer.diskStorage({
  destination: function (req, file, cb) {
    cb(null, uploadsDir);
  },
  filename: function (req, file, cb) {
    const uniqueName = uuidv4() + path.extname(file.originalname);
    cb(null, uniqueName);
  }
});

const fileFilter = (req, file, cb) => {
  const allowed = ['image/jpeg', 'image/png', 'application/pdf'];
  if (allowed.includes(file.mimetype)) return cb(null, true);
  cb(new Error('Only JPG, PNG, or PDF files are allowed'));
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

    // Parse EXIF for images only
    let exif = null;
    let withinGeofence = null;
    if (req.file.mimetype.startsWith('image/')) {
      const fullPath = path.join(uploadsDir, req.file.filename);
      exif = await parseExifFromFile(fullPath);
      // Compute within geofence if PON has coordinates
      const pon = await PON.findById(task.pon);
      if (pon && pon.coordinates && exif && exif.gps) {
        withinGeofence = isWithinGeofence(exif.gps, pon.coordinates, 150);
      }
    }

    // Persist to embedded on task
    const photoData = {
      filename: req.file.filename,
      originalName: req.file.originalname,
      mimeType: req.file.mimetype,
      uploadedBy: req.user.id,
      uploadDate: new Date(),
      exif: exif || undefined,
      withinGeofence: withinGeofence
    };
    task.evidencePhotos.push(photoData);
    await task.save();

    // Persist to Photo collection
    const photoDoc = await Photo.create({
      task: task._id,
      pon: task.pon,
      filename: req.file.filename,
      originalName: req.file.originalname,
      mimeType: req.file.mimetype,
      uploadedBy: req.user.id,
      exif: exif || undefined,
      withinGeofence
    });

    // Update PON status due to photo evidence
    const pon = await PON.findById(task.pon);
    if (pon) {
      await pon.updateProgress();
      await pon.save();
    }

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