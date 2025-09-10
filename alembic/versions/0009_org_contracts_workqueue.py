from alembic import op
import sqlalchemy as sa


revision = "0009_org_contracts_workqueue"
down_revision = "0008_fiber_technical"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "organizations",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("name", sa.String(), nullable=False, unique=True),
        sa.Column("type", sa.String(), nullable=False),  # Civil, Technical, Maintenance, Sales, Main
        sa.Column("active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.add_column("users", sa.Column("org_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=True))
    op.create_foreign_key("fk_users_org", "users", "organizations", ["org_id"], ["id"], ondelete="SET NULL")

    op.create_table(
        "contracts",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("org_id", sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey("organizations.id", ondelete="CASCADE")),
        sa.Column("scope", sa.String(), nullable=False),  # Civil, Technical, Maintenance, Sales
        sa.Column("wards", sa.ARRAY(sa.String()), nullable=True),
        sa.Column("sla_minutes_p1", sa.Integer(), server_default="120", nullable=False),
        sa.Column("sla_minutes_p2", sa.Integer(), server_default="240", nullable=False),
        sa.Column("sla_minutes_p3", sa.Integer(), server_default="1440", nullable=False),
        sa.Column("sla_minutes_p4", sa.Integer(), server_default="4320", nullable=False),
        sa.Column("rate_card_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("start_date", sa.Date(), nullable=True),
        sa.Column("end_date", sa.Date(), nullable=True),
        sa.Column("active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("idx_contracts_org_scope", "contracts", ["org_id", "scope"])

    op.create_table(
        "assignments",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("org_id", sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey("organizations.id", ondelete="CASCADE")),
        sa.Column("scope", sa.String(), nullable=False),      # Civil, Technical, Maintenance, Sales
        sa.Column("pon_id", sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey("pons.id", ondelete="CASCADE"), nullable=True),
        sa.Column("ward", sa.String(), nullable=True),
        sa.Column("priority", sa.Integer(), server_default="100", nullable=False),
        sa.Column("active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.CheckConstraint("(pon_id is not null) or (ward is not null)", name="chk_assignment_target"),
    )
    op.create_index("idx_assignments_scope", "assignments", ["scope"])
    op.create_index("idx_assignments_pon", "assignments", ["pon_id"])
    op.create_index("idx_assignments_ward", "assignments", ["ward"])

    op.add_column("tasks", sa.Column("assigned_org_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=True))
    op.create_foreign_key("fk_tasks_org", "tasks", "organizations", ["assigned_org_id"], ["id"], ondelete="SET NULL")

    op.add_column("incidents", sa.Column("assigned_org_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column("incidents", sa.Column("severity_sla_minutes", sa.Integer(), nullable=True))
    op.add_column("incidents", sa.Column("due_at", sa.DateTime(timezone=True), nullable=True))
    op.create_foreign_key("fk_incidents_org", "incidents", "organizations", ["assigned_org_id"], ["id"], ondelete="SET NULL")
    op.create_index("idx_incidents_due_at", "incidents", ["due_at"])

    # Add PON fields used by work queue if not present
    with op.batch_alter_table("pons") as batch_op:
        try:
            batch_op.add_column(sa.Column("pon_number", sa.String(), nullable=True))
        except Exception:
            pass
        try:
            batch_op.add_column(sa.Column("ward", sa.String(), nullable=True))
        except Exception:
            pass


def downgrade():
    # Remove PON fields if they exist
    with op.batch_alter_table("pons") as batch_op:
        try:
            batch_op.drop_column("ward")
        except Exception:
            pass
        try:
            batch_op.drop_column("pon_number")
        except Exception:
            pass

    op.drop_index("idx_incidents_due_at", table_name="incidents")
    op.drop_constraint("fk_incidents_org", "incidents", type_="foreignkey")
    op.drop_column("incidents", "due_at")
    op.drop_column("incidents", "severity_sla_minutes")
    op.drop_column("incidents", "assigned_org_id")

    op.drop_constraint("fk_tasks_org", "tasks", type_="foreignkey")
    op.drop_column("tasks", "assigned_org_id")

    op.drop_index("idx_assignments_ward", table_name="assignments")
    op.drop_index("idx_assignments_pon", table_name="assignments")
    op.drop_index("idx_assignments_scope", table_name="assignments")
    op.drop_table("assignments")

    op.drop_index("idx_contracts_org_scope", table_name="contracts")
    op.drop_table("contracts")

    op.drop_constraint("fk_users_org", "users", type_="foreignkey")
    op.drop_column("users", "org_id")
    op.drop_table("organizations")

