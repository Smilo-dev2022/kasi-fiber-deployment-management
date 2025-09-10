from typing import List, Optional, Dict


def _decode_polyline(poly: str) -> List[tuple[float, float]]:
    # Accept either encoded polyline or "lat,lng;lat,lng" simple list
    if not poly:
        return []
    if ";" in poly and "," in poly:
        pts: List[tuple[float, float]] = []
        for part in poly.split(";"):
            part = part.strip()
            if not part:
                continue
            lat_str, lng_str = part.split(",")
            pts.append((float(lat_str), float(lng_str)))
        return pts
    # TODO: implement Google polyline decode if required
    return []


def _haversine_m(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    from math import radians, sin, cos, asin, sqrt

    R = 6371000.0
    phi1, phi2 = radians(lat1), radians(lat2)
    dphi = radians(lat2 - lat1)
    dlmb = radians(lng2 - lng1)
    h = sin(dphi / 2) ** 2 + cos(phi1) * cos(phi2) * sin(dlmb / 2) ** 2
    return 2 * R * asin(sqrt(h))


def _segment_project(lat1: float, lng1: float, lat2: float, lng2: float, latp: float, lngp: float) -> tuple[float, float, float]:
    # Approximate projection using equirectangular; sufficient for local spans
    from math import cos, radians

    x1, y1 = radians(lng1) * cos(radians(lat1)), radians(lat1)
    x2, y2 = radians(lng2) * cos(radians(lat2)), radians(lat2)
    xp, yp = radians(lngp) * cos(radians(latp)), radians(latp)
    dx, dy = x2 - x1, y2 - y1
    if dx == 0 and dy == 0:
        return 0.0, lat1, lng1
    t = ((xp - x1) * dx + (yp - y1) * dy) / (dx * dx + dy * dy)
    t_clamped = max(0.0, min(1.0, t))
    # Map back to lat/lng approximately
    y = y1 + t_clamped * dy
    x = x1 + t_clamped * dx
    # Reverse approx
    from math import degrees

    lat = degrees(y)
    lng = degrees(x / cos(y))
    return t_clamped, lat, lng


def snap_distance_to_cable(distance_m: float, cables: List[Dict], cable_hint: Optional[str] = None) -> Optional[Dict]:
    # Pick cable by hint or feeder/distribution preference
    chosen = None
    if cable_hint:
        for c in cables:
            if c.get("code") == cable_hint or c.get("id") == cable_hint:
                chosen = c
                break
    if not chosen:
        feeders = [c for c in cables if str(c.get("type", "")).lower() == "feeder"]
        chosen = feeders[0] if feeders else (cables[0] if cables else None)
    if not chosen:
        return None

    pts = _decode_polyline(chosen.get("polyline", ""))
    if len(pts) < 2:
        return None
    # Walk segments until reaching distance
    traversed = 0.0
    for i in range(len(pts) - 1):
        lat1, lng1 = pts[i]
        lat2, lng2 = pts[i + 1]
        seg_len = _haversine_m(lat1, lng1, lat2, lng2)
        if traversed + seg_len >= distance_m:
            remaining = distance_m - traversed
            t = 0.0 if seg_len == 0 else max(0.0, min(1.0, remaining / seg_len))
            lat = lat1 + (lat2 - lat1) * t
            lng = lng1 + (lng2 - lng1) * t
            return {"cable_id": chosen.get("id"), "lat": lat, "lng": lng, "chainage_m": distance_m}
        traversed += seg_len
    # If beyond end, return last point
    lat, lng = pts[-1]
    return {"cable_id": chosen.get("id"), "lat": lat, "lng": lng, "chainage_m": traversed}

