from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional, Tuple

from PIL import Image, ExifTags


def _get_exif_dict(img: Image.Image) -> dict:
    info = img._getexif() or {}
    tag_map = {ExifTags.TAGS.get(k, k): v for k, v in info.items()}
    return tag_map


def _dms_to_deg(value) -> Optional[float]:
    try:
        d, m, s = value
        return float(d) + float(m) / 60.0 + float(s) / 3600.0
    except Exception:
        return None


def extract_gps_and_datetime(file_bytes: bytes) -> Tuple[Optional[float], Optional[float], Optional[datetime]]:
    with Image.open(BytesIO(file_bytes)) as img:
        exif = _get_exif_dict(img)
        gps_info = exif.get("GPSInfo") or {}
        if isinstance(gps_info, dict):
            # Remap numeric tags if needed
            gps_map = {}
            for k, v in gps_info.items():
                name = ExifTags.GPSTAGS.get(k, k)
                gps_map[name] = v
            gps_info = gps_map
        lat = lng = None
        if gps_info:
            lat = _dms_to_deg(gps_info.get("GPSLatitude"))
            if lat is not None and gps_info.get("GPSLatitudeRef") == "S":
                lat = -lat
            lng = _dms_to_deg(gps_info.get("GPSLongitude"))
            if lng is not None and gps_info.get("GPSLongitudeRef") == "W":
                lng = -lng

        dt: Optional[datetime] = None
        dt_str = exif.get("DateTimeOriginal") or exif.get("DateTime")
        if isinstance(dt_str, bytes):
            dt_str = dt_str.decode("utf-8", errors="ignore")
        if isinstance(dt_str, str):
            # EXIF format: YYYY:MM:DD HH:MM:SS
            try:
                dt = datetime.strptime(dt_str, "%Y:%m:%d %H:%M:%S").replace(tzinfo=timezone.utc)
            except Exception:
                dt = None

        return lat, lng, dt

from io import BytesIO

