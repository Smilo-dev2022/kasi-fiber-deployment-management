from fastapi import APIRouter, Depends
from app.core.deps import require_roles
from app.scheduler import sched


router = APIRouter(prefix="/jobs", tags=["ops"])


@router.get("", dependencies=[Depends(require_roles("ADMIN", "PM", "NOC"))])
def list_jobs():
    jobs = []
    for j in sched.get_jobs():
        jobs.append({
            "id": j.id,
            "next_run_time": j.next_run_time.isoformat() if j.next_run_time else None,
            "trigger": str(j.trigger),
        })
    return jobs

