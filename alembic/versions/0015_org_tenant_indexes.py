from alembic import op
import sqlalchemy as sa


revision = "0015_org_tenant_indexes"
down_revision = "0014_map_postgis"
branch_labels = None
depends_on = None


def upgrade():
    # Add tenant_id and org scoping fields where missing
    op.execute("ALTER TABLE tasks ADD COLUMN IF NOT EXISTS smmme_id uuid")
    # Ensure indexes for heavy endpoints
    op.execute("CREATE INDEX IF NOT EXISTS idx_tasks_sla_due ON tasks (sla_due_at)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_tasks_step_status ON tasks (step, status)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_incidents_org_status ON incidents (assigned_org_id, status)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_photos_pon_time ON photos (pon_id, taken_ts)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_otdr_plan ON otdr_results (test_plan_id)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_lspm_plan ON lspm_results (test_plan_id)")


def downgrade():
    op.execute("DROP INDEX IF EXISTS idx_lspm_plan")
    op.execute("DROP INDEX IF EXISTS idx_otdr_plan")
    op.execute("DROP INDEX IF EXISTS idx_photos_pon_time")
    op.execute("DROP INDEX IF EXISTS idx_incidents_org_status")
    op.execute("DROP INDEX IF EXISTS idx_tasks_step_status")
    op.execute("DROP INDEX IF EXISTS idx_tasks_sla_due")

