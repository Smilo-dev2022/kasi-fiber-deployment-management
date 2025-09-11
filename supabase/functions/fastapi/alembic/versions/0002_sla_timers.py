from alembic import op
import sqlalchemy as sa

revision = "0002_sla_timers"
down_revision = "0001_init"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("tasks", sa.Column("sla_minutes", sa.Integer(), nullable=True))
    op.add_column("tasks", sa.Column("sla_due_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("tasks", sa.Column("breached", sa.Boolean(), server_default=sa.text("false"), nullable=False))
    op.add_column("pons", sa.Column("sla_breaches", sa.Integer(), server_default="0", nullable=False))
    op.create_index("idx_tasks_sla_due_at", "tasks", ["sla_due_at"]) 
    op.create_index("idx_tasks_breached", "tasks", ["breached"]) 


def downgrade():
    op.drop_index("idx_tasks_breached", table_name="tasks")
    op.drop_index("idx_tasks_sla_due_at", table_name="tasks")
    op.drop_column("pons", "sla_breaches")
    op.drop_column("tasks", "breached")
    op.drop_column("tasks", "sla_due_at")
    op.drop_column("tasks", "sla_minutes")

