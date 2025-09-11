from alembic import op
import sqlalchemy as sa


revision = "0015_perf_indexes_and_cache"
down_revision = "0014_map_postgis"
branch_labels = None
depends_on = None


def upgrade():
    # Work-queue performance: tasks by step/status and sla_due_at ordering
    op.create_index("idx_tasks_step_status", "tasks", ["step", "status"], postgresql_where=sa.text("status is not null"))
    op.create_index("idx_tasks_sla_due_at_notnull", "tasks", ["sla_due_at"], postgresql_where=sa.text("sla_due_at is not null"))
    # Assignments lookup by org and step
    op.create_index("idx_assignments_org_step", "assignments", ["org_id", "step_type"])
    # Photos validated lookup per PON
    op.create_index("idx_photos_valid_pon", "photos", ["pon_id"], postgresql_where=sa.text("exif_ok and within_geofence"))


def downgrade():
    op.drop_index("idx_photos_valid_pon", table_name="photos")
    op.drop_index("idx_assignments_org_step", table_name="assignments")
    op.drop_index("idx_tasks_sla_due_at_notnull", table_name="tasks")
    op.drop_index("idx_tasks_step_status", table_name="tasks")

