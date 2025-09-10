const mongoose = require('mongoose');

const PhotoSchema = new mongoose.Schema({
  task: { type: mongoose.Schema.Types.ObjectId, ref: 'Task', required: true, index: true },
  pon: { type: mongoose.Schema.Types.ObjectId, ref: 'PON', required: true, index: true },
  filename: { type: String, required: true },
  originalName: { type: String, required: true },
  mimeType: { type: String, required: true },
  uploadedBy: { type: mongoose.Schema.Types.ObjectId, ref: 'User', required: true },
  uploadDate: { type: Date, default: Date.now },
  exif: {
    gps: {
      latitude: Number,
      longitude: Number
    },
    takenTs: Date
  },
  withinGeofence: { type: Boolean, default: null }
}, { timestamps: true });

PhotoSchema.index({ pon: 1, 'exif.takenTs': 1 });

module.exports = mongoose.model('Photo', PhotoSchema);

