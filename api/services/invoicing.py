from sqlalchemy.orm import Session
from ..models.invoice import Invoice
from ..models.photo import Photo
from ..models.task import Task


def can_submit_invoice(db: Session, pon_id: int) -> bool:
    required_kinds = {"Dig", "Plant", "CAC", "Stringing"}
    kinds = {k for (k,) in db.query(Photo.kind).filter(Photo.pon_id == pon_id).distinct()}
    if not required_kinds.issubset(kinds):
        return False
    steps_required = {"PolePlanting", "CAC", "Stringing"}
    done_steps = {t.step for t in db.query(Task).filter(Task.pon_id == pon_id, Task.status == "Done").all()}
    return steps_required.issubset(done_steps)

