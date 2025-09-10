function toRadians(degrees) {
  return degrees * Math.PI / 180;
}

function haversineDistanceMeters(coordA, coordB) {
  const R = 6371000; // meters
  const dLat = toRadians(coordB.latitude - coordA.latitude);
  const dLon = toRadians(coordB.longitude - coordA.longitude);
  const lat1 = toRadians(coordA.latitude);
  const lat2 = toRadians(coordB.latitude);

  const a = Math.sin(dLat / 2) * Math.sin(dLat / 2) +
            Math.sin(dLon / 2) * Math.sin(dLon / 2) * Math.cos(lat1) * Math.cos(lat2);
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
  return R * c;
}

function isWithinRadiusMeters(coordA, coordB, radiusMeters) {
  if (!coordA || !coordB ||
      typeof coordA.latitude !== 'number' || typeof coordA.longitude !== 'number' ||
      typeof coordB.latitude !== 'number' || typeof coordB.longitude !== 'number') {
    return false;
  }
  return haversineDistanceMeters(coordA, coordB) <= radiusMeters;
}

module.exports = { haversineDistanceMeters, isWithinRadiusMeters };

