const mongoose = require('mongoose');

const PhotoSchema = new mongoose.Schema({
  task: {
    type: mongoose.Schema.Types.ObjectId,
    ref: 'Task',
    required: true
  },
  filename: String,
  originalName: String,
  uploadedBy: { type: mongoose.Schema.Types.ObjectId, ref: 'User' },
  uploadDate: { type: Date, default: Date.now },
  pon: { type: mongoose.Schema.Types.ObjectId, ref: 'PON' },
  exif: {
    gpsLatitude: Number,
    gpsLongitude: Number,
    dateTimeOriginal: Date,
    withinGeofence: Boolean
  }
}, { timestamps: true });

PhotoSchema.index({ pon: 1, uploadDate: -1 });
PhotoSchema.index({ task: 1 });

module.exports = mongoose.model('Photo', PhotoSchema);

