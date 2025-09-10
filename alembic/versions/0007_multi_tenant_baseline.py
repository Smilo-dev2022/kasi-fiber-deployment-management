from alembic import op
import sqlalchemy as sa

revision = "0007_multi_tenant_baseline"
down_revision = "0006_rates_paysheets"
branch_labels = None
depends_on = None


def upgrade():
    # New tables
    op.create_table(
        "tenants",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("code", sa.String(), nullable=False, unique=True),
        sa.Column("plan", sa.String(), nullable=False, server_default="Starter"),
        sa.Column("status", sa.String(), nullable=False, server_default="Active"),
        sa.Column("flags", sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")),
        sa.Column("created_at", sa.DateTime(timezone=True)),
        sa.Column("updated_at", sa.DateTime(timezone=True)),
    )

    op.create_table(
        "tenant_domains",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("domain", sa.String(), nullable=False),
        sa.Column("is_primary", sa.Boolean(), nullable=False, server_default=sa.text("false")),
    )
    op.create_unique_constraint("uq_tenant_domain_domain", "tenant_domains", ["domain"]) 

    op.create_table(
        "tenant_themes",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("theme", sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")),
        sa.Column("logo_url", sa.String(), nullable=True),
        sa.Column("favicon_url", sa.String(), nullable=True),
        sa.Column("pdf_footer", sa.String(), nullable=True),
    )

    op.create_table(
        "feature_flags",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("key", sa.String(), nullable=False),
        sa.Column("value", sa.Boolean(), nullable=False, server_default=sa.text("false")),
    )
    op.create_unique_constraint("uq_feature_flag_key", "feature_flags", ["tenant_id", "key"]) 

    op.create_table(
        "audit_logs",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("actor_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("actor_email", sa.String(), nullable=True),
        sa.Column("action", sa.String(), nullable=False),
        sa.Column("resource", sa.String(), nullable=True),
        sa.Column("resource_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("ip", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True)),
    )

    op.create_table(
        "metering_counters",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("metric", sa.String(), nullable=False),
        sa.Column("period", sa.String(), nullable=False),
        sa.Column("value", sa.BigInteger(), nullable=False),
    )
    op.create_unique_constraint("uq_metering_counter", "metering_counters", ["tenant_id", "metric", "period"]) 

    op.create_table(
        "tenant_file_keys",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("kms_key_arn", sa.String(), nullable=True),
        sa.Column("storage_prefix", sa.String(), nullable=False),
    )

    # Add tenant_id to existing tables
    for table in ["pons", "smmes", "photos", "tasks", "cac_checks", "assets", "rate_cards", "pay_sheets", "pay_sheet_lines"]:
        try:
            op.add_column(table, sa.Column("tenant_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=True))
        except Exception:
            pass

    # Backfill to a default tenant if needed is left to ops scripts
    # After backfill, set NOT NULL
    for table in ["pons", "smmes", "photos", "tasks", "cac_checks", "assets", "rate_cards", "pay_sheets", "pay_sheet_lines"]:
        try:
            op.alter_column(table, "tenant_id", nullable=False)
        except Exception:
            pass

    # Indexes to speed up RLS filters
    for table in ["pons", "smmes", "photos", "tasks", "cac_checks", "assets", "rate_cards", "pay_sheets", "pay_sheet_lines"]:
        try:
            op.create_index(f"idx_{table}_tenant", table, ["tenant_id"])
        except Exception:
            pass

    # Enable RLS and add policies
    rls_tables = [
        "tenants", "tenant_domains", "tenant_themes", "feature_flags", "audit_logs",
        "metering_counters", "tenant_file_keys",
        "pons", "smmes", "photos", "tasks", "cac_checks", "assets", "rate_cards", "pay_sheets", "pay_sheet_lines"
    ]

    for t in rls_tables:
        try:
            op.execute(f"ALTER TABLE {t} ENABLE ROW LEVEL SECURITY")
        except Exception:
            pass

    def add_policies(table: str):
        using = "(tenant_id = current_setting('app.tenant_id')::uuid)"
        try:
            op.execute(f"CREATE POLICY {table}_tenant_select ON {table} FOR SELECT USING {using}")
        except Exception:
            pass
        try:
            op.execute(f"CREATE POLICY {table}_tenant_update ON {table} FOR UPDATE USING {using} WITH CHECK {using}")
        except Exception:
            pass
        try:
            op.execute(f"CREATE POLICY {table}_tenant_insert ON {table} FOR INSERT WITH CHECK {using}")
        except Exception:
            pass
        # Set default tenant_id from app setting if column exists
        try:
            op.execute(f"ALTER TABLE {table} ALTER COLUMN tenant_id SET DEFAULT (current_setting('app.tenant_id', true))::uuid")
        except Exception:
            pass

    for t in rls_tables:
        add_policies(t)


def downgrade():
    for table in ["pons", "smmes", "photos", "tasks", "cac_checks", "assets", "rate_cards", "pay_sheets", "pay_sheet_lines"]:
        try:
            op.drop_index(f"idx_{table}_tenant", table_name=table)
        except Exception:
            pass
        try:
            op.drop_column(table, "tenant_id")
        except Exception:
            pass

    # Drop RLS policies
    rls_tables = [
        "tenants", "tenant_domains", "tenant_themes", "feature_flags", "audit_logs",
        "metering_counters", "tenant_file_keys",
        "pons", "smmes", "photos", "tasks", "cac_checks", "assets", "rate_cards", "pay_sheets", "pay_sheet_lines"
    ]
    for t in rls_tables:
        # best effort drops
        for suffix in ["tenant_insert", "tenant_update", "tenant_select"]:
            try:
                op.execute(f"DROP POLICY IF EXISTS {t}_{suffix} ON {t}")
            except Exception:
                pass

    op.drop_table("tenant_file_keys")
    op.drop_constraint("uq_metering_counter", "metering_counters")
    op.drop_table("metering_counters")
    op.drop_table("audit_logs")
    op.drop_constraint("uq_feature_flag_key", "feature_flags")
    op.drop_table("feature_flags")
    op.drop_table("tenant_themes")
    op.drop_constraint("uq_tenant_domain_domain", "tenant_domains")
    op.drop_table("tenant_domains")
    op.drop_table("tenants")

