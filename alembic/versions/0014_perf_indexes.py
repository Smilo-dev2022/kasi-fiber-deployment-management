from alembic import op
import sqlalchemy as sa


revision = "0014_perf_indexes"
down_revision = "0013_spares_inventory"
branch_labels = None
depends_on = None


def upgrade():
    # Incidents: (assigned_org_id, status, due_at)
    try:
        op.create_index("idx_incidents_org_status_due", "incidents", ["assigned_org_id", "status", "due_at"], unique=False)
    except Exception:
        pass
    # Tasks: (assigned_org_id -> smmme_id), status, sla_due_at
    try:
        op.create_index("idx_tasks_smme_status_sla", "tasks", ["smmme_id", "status", "sla_due_at"], unique=False)
    except Exception:
        pass
    # Certificate Acceptance: (pon_id, checked_at)
    try:
        op.create_index("idx_certificate_acceptance_pon_checked", "certificate_acceptance", ["pon_id", "checked_at"], unique=False)
    except Exception:
        pass
    # Stringing runs: (pon_id, end_ts)
    try:
        op.create_index("idx_stringing_runs_pon_end", "stringing_runs", ["pon_id", "end_ts"], unique=False)
    except Exception:
        pass


def downgrade():
    for name, table in [
        ("idx_stringing_runs_pon_end", "stringing_runs"),
        ("idx_certificate_acceptance_pon_checked", "certificate_acceptance"),
        ("idx_tasks_smme_status_sla", "tasks"),
        ("idx_incidents_org_status_due", "incidents"),
    ]:
        try:
            op.drop_index(name, table_name=table)
        except Exception:
            pass

