from alembic import op
import sqlalchemy as sa


revision = "0014_stringing_indexes"
down_revision = "0013_spares_inventory"
branch_labels = None
depends_on = None


def upgrade():
    try:
        op.create_index("idx_stringing_runs_pon_end", "stringing_runs", ["pon_id", "completed_at"]) 
    except Exception:
        # Table may not exist in all environments
        pass


def downgrade():
    try:
        op.drop_index("idx_stringing_runs_pon_end", table_name="stringing_runs")
    except Exception:
        pass

