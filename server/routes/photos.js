const express = require('express');
const multer = require('multer');
const path = require('path');
const { v4: uuidv4 } = require('uuid');
const Task = require('../models/Task');
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

    // Add photo to task
    const photoData = {
      filename: req.file.filename,
      originalName: req.file.originalname,
      uploadedBy: req.user.id,
      uploadDate: new Date()
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