const fs = require('fs');
const exifr = require('exifr');

async function parseExifFromFile(filePath) {
  try {
    const data = await exifr.parse(filePath, { tiff: true, ifd0: true, exif: true, gps: true });
    if (!data) return null;
    const latitude = (data.latitude !== undefined ? data.latitude : (data.gps && data.gps.latitude));
    const longitude = (data.longitude !== undefined ? data.longitude : (data.gps && data.gps.longitude));
    const takenTs = data.DateTimeOriginal || data.CreateDate || data.ModifyDate || null;
    return {
      gps: (latitude != null && longitude != null) ? { latitude, longitude } : null,
      takenTs: takenTs ? new Date(takenTs) : null
    };
  } catch (err) {
    return null;
  }
}

function isWithinGeofence(point, center, radiusMeters = 100) {
  if (!point || !center || point.latitude == null || center.latitude == null) return false;
  const toRad = d => d * Math.PI / 180;
  const R = 6371000;
  const dLat = toRad(point.latitude - center.latitude);
  const dLon = toRad(point.longitude - center.longitude);
  const lat1 = toRad(center.latitude);
  const lat2 = toRad(point.latitude);
  const a = Math.sin(dLat/2) * Math.sin(dLat/2) + Math.sin(dLon/2) * Math.sin(dLon/2) * Math.cos(lat1) * Math.cos(lat2);
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
  const distance = R * c;
  return distance <= radiusMeters;
}

module.exports = { parseExifFromFile, isWithinGeofence };

