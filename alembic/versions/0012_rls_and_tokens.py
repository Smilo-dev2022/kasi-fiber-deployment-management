from alembic import op
import sqlalchemy as sa


revision = "0012_rls_and_tokens"
down_revision = "0011_spares"
branch_labels = None
depends_on = None


def upgrade():
    # API tokens scoped per org
    op.create_table(
        "api_tokens",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("org_id", sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey("organizations.id", ondelete="CASCADE")),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("token_hash", sa.String(), nullable=False),
        sa.Column("scope", sa.String(), nullable=False),  # read, write, finance
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True)),
        sa.Column("revoked", sa.Boolean(), server_default=sa.text("false"), nullable=False),
    )
    op.create_index("idx_api_tokens_org", "api_tokens", ["org_id"]) 

    # RLS policies: enable and add tenant/org policies for select/insert
    tables = [
        "devices",
        "incidents",
        "topo_nodes",
        "topo_edges",
        "maint_windows",
        "device_configs",
        "golden_templates",
        "stores",
        "spare_issues",
        "spare_returns",
        "organizations",
        "contracts",
        "assignments",
    ]
    for t in tables:
        op.execute(f"ALTER TABLE {t} ENABLE ROW LEVEL SECURITY")
        # Define permissive policies referencing current_setting('app.tenant_id')
        # Note: application must set these settings per request
        op.execute(
            f"CREATE POLICY {t}_tenant_select ON {t} FOR SELECT USING (tenant_id IS NULL OR tenant_id = current_setting('app.tenant_id', true)::uuid)"
        )
        op.execute(
            f"CREATE POLICY {t}_tenant_insert ON {t} FOR INSERT WITH CHECK (tenant_id IS NULL OR tenant_id = current_setting('app.tenant_id', true)::uuid)"
        )


def downgrade():
    op.drop_table("api_tokens")
    # Policies are dropped with table or can be dropped explicitly if needed

