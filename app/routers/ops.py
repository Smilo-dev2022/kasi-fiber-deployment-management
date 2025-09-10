import os
import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.deps import get_db
from app.scheduler import sched
from app.services.s3 import get_client as get_s3_client, settings as s3_settings


router = APIRouter(prefix="/ops", tags=["ops"]) 


def _read_latest_alembic_revision() -> Optional[str]:
    versions_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "alembic", "versions")
    try:
        files = [f for f in os.listdir(versions_dir) if f.endswith(".py")]
    except Exception:
        return None
    if not files:
        return None
    latest_rev: Optional[str] = None
    for fname in sorted(files):
        fpath = os.path.join(versions_dir, fname)
        try:
            with open(fpath, "r") as fh:
                content = fh.read()
            m = re.search(r'^revision\s*=\s*"([^"]+)"', content, re.MULTILINE)
            if m:
                latest_rev = m.group(1)
        except Exception:
            continue
    return latest_rev


@router.get("/scheduler/jobs")
def list_scheduler_jobs() -> List[Dict[str, Any]]:
    jobs = sched.get_jobs()
    out: List[Dict[str, Any]] = []
    for j in jobs:
        out.append(
            {
                "id": j.id,
                "name": getattr(j, "name", None),
                "trigger": str(j.trigger),
                "next_run_time": j.next_run_time.isoformat() if j.next_run_time else None,
            }
        )
    return out


@router.get("/readiness")
def readiness(db: Session = Depends(get_db)) -> Dict[str, Any]:
    checks: Dict[str, Dict[str, Any]] = {}

    # Migrations
    expected = _read_latest_alembic_revision()
    db_rev: Optional[str] = None
    try:
        row = db.execute(text("select version_num from alembic_version"))
        db_rev = row.scalar()  # type: ignore[assignment]
    except Exception as exc:
        checks["alembic"] = {"status": "fail", "detail": f"alembic_version missing: {exc}"}
    else:
        if expected and db_rev == expected:
            checks["alembic"] = {"status": "ok", "detail": f"{db_rev}"}
        else:
            checks["alembic"] = {"status": "warn", "detail": f"db={db_rev} expected={expected}"}

    # Seeded data
    try:
        orgs = db.execute(text("select count(1) from organizations")).scalar() or 0
        contracts = db.execute(text("select count(1) from contracts")).scalar() or 0
        assigns = db.execute(text("select count(1) from assignments")).scalar() or 0
        seeded_ok = (orgs > 0) and (contracts > 0) and (assigns > 0)
        checks["seeded_data"] = {
            "status": "ok" if seeded_ok else "fail",
            "detail": {"organizations": orgs, "contracts": contracts, "assignments": assigns},
        }
    except Exception as exc:
        checks["seeded_data"] = {"status": "fail", "detail": str(exc)}

    # Webhook security
    hmac_secret = os.getenv("NMS_HMAC_SECRET")
    allow_ips = [x.strip() for x in os.getenv("NMS_ALLOW_IPS", "").split(",") if x.strip()]
    if hmac_secret and allow_ips:
        checks["webhook_security"] = {"status": "ok", "detail": {"allow_ips": len(allow_ips)}}
    else:
        checks["webhook_security"] = {
            "status": "fail",
            "detail": {
                "NMS_HMAC_SECRET": bool(hmac_secret),
                "NMS_ALLOW_IPS": len(allow_ips),
            },
        }

    # Scheduler jobs present
    jobs = sched.get_jobs()
    checks["scheduler_jobs"] = {"status": "ok" if jobs else "fail", "detail": [j.id for j in jobs]}

    # Backups (signal via env)
    last_ok = os.getenv("BACKUP_LAST_OK_TS")
    checks["backups"] = {"status": "ok" if last_ok else "warn", "detail": last_ok or "missing BACKUP_LAST_OK_TS"}

    # CORS
    cors_env = os.getenv("CORS_ALLOW_ORIGINS", "*")
    origins = [o.strip() for o in cors_env.split(",") if o.strip()]
    checks["cors"] = {
        "status": "ok" if origins and origins != ["*"] else "warn",
        "detail": origins,
    }

    # File guards config
    max_mb = int(os.getenv("PHOTO_MAX_MB", "0") or 0)
    allowed_types = [t.strip() for t in os.getenv("PHOTO_ALLOWED_TYPES", "").split(",") if t.strip()]
    checks["photo_guards_configured"] = {
        "status": "ok" if (max_mb > 0 and allowed_types) else "fail",
        "detail": {"PHOTO_MAX_MB": max_mb, "PHOTO_ALLOWED_TYPES": allowed_types},
    }

    # S3 lifecycle rules
    try:
        s3 = get_s3_client()
        lifecycle = s3.get_bucket_lifecycle_configuration(Bucket=s3_settings.S3_BUCKET)
        rules = lifecycle.get("Rules", []) if lifecycle else []
        checks["s3_lifecycle"] = {"status": "ok" if rules else "fail", "detail": len(rules)}
    except Exception as exc:
        checks["s3_lifecycle"] = {"status": "warn", "detail": str(exc)}

    # Incidents routing and due_at
    try:
        with_due = db.execute(text("select count(1) from incidents where due_at is not null"))
        cnt = with_due.scalar() or 0
        checks["incidents_due_at"] = {"status": "ok" if cnt > 0 else "warn", "detail": cnt}
    except Exception as exc:
        checks["incidents_due_at"] = {"status": "warn", "detail": str(exc)}

    # Recent NMS alerts
    try:
        cnt_recent = db.execute(
            text(
                """
            select count(1) from incidents
            where nms_ref is not null and opened_at >= (now() at time zone 'utc') - interval '1 day'
            """
            )
        ).scalar() or 0
        checks["nms_recent_alerts"] = {"status": "ok" if cnt_recent > 0 else "warn", "detail": cnt_recent}
    except Exception as exc:
        checks["nms_recent_alerts"] = {"status": "warn", "detail": str(exc)}

    # Photos EXIF/geofence
    try:
        cnt_good = db.execute(text("select count(1) from photos where exif_ok = true and within_geofence = true"))
        cnt_good_val = cnt_good.scalar() or 0
        checks["photos_exif_geofence"] = {"status": "ok" if cnt_good_val > 0 else "warn", "detail": cnt_good_val}
    except Exception as exc:
        checks["photos_exif_geofence"] = {"status": "warn", "detail": str(exc)}

    # Performance indexes (spot checks)
    try:
        idx_checks = []
        # tasks.sla_due_at index
        x = db.execute(
            text(
                """
            select 1 from pg_indexes where tablename = 'tasks' and indexname = 'idx_tasks_sla_due_at'
            """
            )
        ).first()
        idx_checks.append(bool(x))
        # incidents severity/opened index
        y = db.execute(
            text(
                """
            select 1 from pg_indexes where tablename = 'incidents' and indexname = 'idx_incidents_severity_opened'
            """
            )
        ).first()
        idx_checks.append(bool(y))
        checks["indexes_present"] = {"status": "ok" if all(idx_checks) else "fail", "detail": idx_checks}
    except Exception as exc:
        checks["indexes_present"] = {"status": "warn", "detail": str(exc)}

    # Security signals
    checks["security_env"] = {
        "status": "ok"
        if (os.getenv("JWT_SECRET") and (os.getenv("VAULT_ADDR") or os.getenv("AWS_REGION")))
        else "warn",
        "detail": {
            "JWT_SECRET": bool(os.getenv("JWT_SECRET")),
            "VAULT": bool(os.getenv("VAULT_ADDR")),
            "AWS_REGION": bool(os.getenv("AWS_REGION")),
        },
    }

    # Coverage signal (from CI or artifact)
    cov = os.getenv("LATEST_COVERAGE")
    checks["tests_coverage"] = {"status": "ok" if cov and float(cov) >= 80.0 else "warn", "detail": cov or "n/a"}

    # Overall
    status_order = {"fail": 0, "warn": 1, "ok": 2}
    worst = min((status_order.get(v.get("status", "warn"), 1) for v in checks.values()), default=1)
    overall = [k for k, v in status_order.items() if v == worst][0]

    return {
        "ts": datetime.now(timezone.utc).isoformat(),
        "overall": overall,
        "checks": checks,
        "s3_bucket": s3_settings.S3_BUCKET,
        "cors": os.getenv("CORS_ALLOW_ORIGINS", "*") or "*",
    }

