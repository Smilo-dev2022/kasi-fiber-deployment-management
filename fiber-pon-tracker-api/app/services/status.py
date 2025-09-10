from sqlalchemy.orm import Session
from app.models.pon import PON
from app.models.task import Task
from app.models.cac import CACCheck
from app.models.photo import Photo


def compute_status(db: Session, pon: PON):
    tasks = db.query(Task).filter(Task.pon_id == pon.id).all()
    cacs = db.query(CACCheck).filter(CACCheck.pon_id == pon.id).all()
    photos = db.query(Photo).filter(Photo.pon_id == pon.id).all()

    done_caps = len(cacs) > 0 and all(bool(c.passed) for c in cacs)
    photos_ok = len(photos) > 0
    stringing_ok = bool(pon.stringing_done)
    poles_ok = pon.poles_planted >= pon.poles_planned and pon.poles_planned > 0

    if poles_ok and done_caps and stringing_ok and photos_ok:
        return "Completed"
    if any(t.status in ("In Progress","Done") for t in tasks):
        return "In Progress"
    return "Not Started"
