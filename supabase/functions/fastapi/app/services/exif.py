from io import BytesIO
from datetime import datetime, timezone
from typing import Optional

from PIL import Image
import exifread


def _to_deg(value) -> float:
    d = float(value[0].num) / float(value[0].den)
    m = float(value[1].num) / float(value[1].den)
    s = float(value[2].num) / float(value[2].den)
    return d + (m / 60.0) + (s / 3600.0)


def parse_exif(stream: bytes) -> dict:
    """Return dict: taken_ts (UTC), gps_lat, gps_lng."""
    out: dict[str, Optional[float | datetime]] = {"taken_ts": None, "gps_lat": None, "gps_lng": None}
    bio = BytesIO(stream)

    # Try PIL DateTimeOriginal
    try:
        img = Image.open(bio)
        exif = img.getexif()
        dto = exif.get(36867)  # DateTimeOriginal
        if dto:
            ts = datetime.strptime(str(dto), "%Y:%m:%d %H:%M:%S").replace(tzinfo=timezone.utc)
            out["taken_ts"] = ts
    except Exception:
        pass

    # Reset stream for exifread
    bio.seek(0)
    try:
        tags = exifread.process_file(bio, details=False)
        # Fallback DateTimeOriginal
        if not out["taken_ts"]:
            dto = tags.get("EXIF DateTimeOriginal")
            if dto:
                ts = datetime.strptime(str(dto), "%Y:%m:%d %H:%M:%S").replace(tzinfo=timezone.utc)
                out["taken_ts"] = ts
        # GPS
        lat_ref = tags.get("GPS GPSLatitudeRef")
        lat_val = tags.get("GPS GPSLatitude")
        lon_ref = tags.get("GPS GPSLongitudeRef")
        lon_val = tags.get("GPS GPSLongitude")
        if lat_ref and lat_val and lon_ref and lon_val:
            lat = _to_deg(lat_val.values)
            lon = _to_deg(lon_val.values)
            if str(lat_ref.values).upper().startswith("S"):
                lat = -lat
            if str(lon_ref.values).upper().startswith("W"):
                lon = -lon
            out["gps_lat"] = round(lat, 6)
            out["gps_lng"] = round(lon, 6)
    except Exception:
        pass

    return out

