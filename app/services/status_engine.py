from __future__ import annotations

import logging
from typing import Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.pon import PON
from app.models.task import Task
from app.models.cac import CACCheck
from app.models.photo import Photo


log = logging.getLogger(__name__)


def recompute_pon_status(db: Session, pon_id) -> Optional[str]:
    pon: PON | None = db.get(PON, pon_id)
    if not pon:
        return None
    before = pon.status or "Unknown"

    total_tasks = db.query(func.count(Task.id)).filter(Task.pon_id == pon_id).scalar() or 0
    done_tasks = db.query(func.count(Task.id)).filter(Task.pon_id == pon_id, Task.status == "Done").scalar() or 0
    any_cac = db.query(func.count(CACCheck.id)).filter(CACCheck.pon_id == pon_id).scalar() or 0
    any_valid_photo = (
        db.query(func.count(Photo.id))
        .filter(Photo.pon_id == pon_id, Photo.within_geofence == True, Photo.exif_ok == True)
        .scalar()
        or 0
    )

    after = "In Progress"
    if total_tasks > 0 and done_tasks == total_tasks and any_cac > 0 and any_valid_photo > 0:
        after = "Completed"

    if before != after:
        pon.status = after
        db.commit()
        log.info("PON status transition", extra={"pon_id": str(pon_id), "before": before, "after": after})
    return after

