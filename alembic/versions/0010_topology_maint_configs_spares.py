from alembic import op
import sqlalchemy as sa


revision = "0010_topology_maint_configs_spares"
down_revision = "0009_access_ops"
branch_labels = None
depends_on = None


def upgrade():
    # Topology nodes and edges
    op.create_table(
        "topo_nodes",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("pon_id", sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey("pons.id", ondelete="CASCADE")),
        sa.Column("type", sa.String(), nullable=False),
        sa.Column("code", sa.String(), nullable=False),
        sa.Column("gps_lat", sa.Numeric(9, 6)),
        sa.Column("gps_lng", sa.Numeric(9, 6)),
    )
    op.create_index("idx_topo_nodes_pon", "topo_nodes", ["pon_id"]) 
    op.create_index("idx_topo_nodes_code", "topo_nodes", ["code"]) 

    op.create_table(
        "topo_edges",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("pon_id", sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey("pons.id", ondelete="CASCADE")),
        sa.Column("a_id", sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey("topo_nodes.id", ondelete="CASCADE")),
        sa.Column("b_id", sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey("topo_nodes.id", ondelete="CASCADE")),
        sa.Column("cable_code", sa.String()),
        sa.Column("length_m", sa.Numeric()),
    )
    op.create_index("idx_topo_edges_pon", "topo_edges", ["pon_id"]) 
    op.create_index("idx_topo_edges_nodes", "topo_edges", ["a_id", "b_id"]) 

    # Maintenance windows
    op.create_table(
        "maint_windows",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("scope", sa.String(), nullable=False),
        sa.Column("target_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("start_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("end_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("approved_by", sa.String()),
    )
    op.create_index("idx_maint_scope", "maint_windows", ["scope", "target_id"]) 

    # Device configs and golden templates
    op.create_table(
        "device_configs",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("device_id", sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey("devices.id", ondelete="CASCADE")),
        sa.Column("source", sa.String(), nullable=False),
        sa.Column("collected_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("version", sa.String()),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("sha256", sa.String(), nullable=False),
    )
    op.create_index("idx_device_configs_device", "device_configs", ["device_id", "collected_at"]) 

    op.create_table(
        "golden_templates",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("role", sa.String()),
        sa.Column("vendor", sa.String()),
        sa.Column("model", sa.String()),
        sa.Column("template", sa.Text(), nullable=False),
    )
    op.create_index("idx_golden_template_match", "golden_templates", ["role", "vendor", "model"]) 

    # RLS enablement for new tables
    op.execute("ALTER TABLE topo_nodes ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE topo_edges ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE maint_windows ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE device_configs ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE golden_templates ENABLE ROW LEVEL SECURITY")


def downgrade():
    op.drop_index("idx_golden_template_match", table_name="golden_templates")
    op.drop_table("golden_templates")

    op.drop_index("idx_device_configs_device", table_name="device_configs")
    op.drop_table("device_configs")

    op.drop_index("idx_maint_scope", table_name="maint_windows")
    op.drop_table("maint_windows")

    op.drop_index("idx_topo_edges_nodes", table_name="topo_edges")
    op.drop_index("idx_topo_edges_pon", table_name="topo_edges")
    op.drop_table("topo_edges")

    op.drop_index("idx_topo_nodes_code", table_name="topo_nodes")
    op.drop_index("idx_topo_nodes_pon", table_name="topo_nodes")
    op.drop_table("topo_nodes")

