from sqlalchemy.orm import Session

from ..models.pon import PON
from ..models.cac import CACCheck
from ..models.photo import Photo
from ..models.stringing import StringingRun
from ..models.task import Task


REQUIRED_PHOTO_KINDS = {"Dig", "Plant", "CAC", "Stringing"}


def compute_photos_uploaded(db: Session, pon_id: int) -> bool:
    kinds = {k for (k,) in db.query(Photo.kind).filter(Photo.pon_id == pon_id).distinct()}
    return REQUIRED_PHOTO_KINDS.issubset(kinds)


def compute_cac_passed(db: Session, pon_id: int) -> bool:
    checks = db.query(CACCheck).filter(CACCheck.pon_id == pon_id).all()
    if not checks:
        return False
    return all(c.passed for c in checks)


def compute_stringing_done(db: Session, pon_id: int, planned_meters: float | None = None) -> bool:
    runs = db.query(StringingRun).filter(StringingRun.pon_id == pon_id).all()
    if not runs:
        return False
    if planned_meters is None:
        return True
    total = sum(r.meters for r in runs)
    return total >= planned_meters


def update_pon_status(db: Session, pon: PON) -> PON:
    pon.photos_uploaded = compute_photos_uploaded(db, pon.id)
    pon.cac_passed = compute_cac_passed(db, pon.id)
    # planned meters not modeled; use stringing_done if any run exists
    pon.stringing_done = compute_stringing_done(db, pon.id, None)

    if (
        pon.poles_planted == pon.poles_planned
        and pon.poles_planned > 0
        and pon.cac_passed
        and pon.stringing_done
        and pon.photos_uploaded
    ):
        pon.status = "Completed"
    else:
        # In Progress when any task is In Progress or Done
        has_active_task = (
            db.query(Task)
            .filter(Task.pon_id == pon.id, Task.status.in_(["In Progress", "Done"]))
            .first()
            is not None
        )
        if has_active_task:
            pon.status = "In Progress"
        else:
            pon.status = "Not Started"

    return pon

