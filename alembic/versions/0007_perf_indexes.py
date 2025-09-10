from alembic import op
import sqlalchemy as sa

revision = "0007_perf_indexes"
down_revision = "0006_rates_paysheets"
branch_labels = None
depends_on = None


def upgrade():
    op.create_index("idx_pons_status_ward", "pons", ["status", "ward"], if_not_exists=True)  # type: ignore[arg-type]
    op.create_index("idx_tasks_pon_breached", "tasks", ["pon_id", "breached"], if_not_exists=True)  # type: ignore[arg-type]
    op.create_index("idx_photos_pon_taken", "photos", ["pon_id", "taken_ts"], if_not_exists=True)  # type: ignore[arg-type]
    op.create_index("idx_assets_code_status", "assets", ["code", "status"], if_not_exists=True)  # type: ignore[arg-type]


def downgrade():
    op.drop_index("idx_assets_code_status", table_name="assets")
    op.drop_index("idx_photos_pon_taken", table_name="photos")
    op.drop_index("idx_tasks_pon_breached", table_name="tasks")
    op.drop_index("idx_pons_status_ward", table_name="pons")

