from alembic import op
import sqlalchemy as sa


revision = "0010_topology_core"
down_revision = "0009_access_ops"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "topo_nodes",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("type", sa.String(), nullable=False),
        sa.Column("code", sa.String(), nullable=False),
        sa.Column("pon_id", sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey("pons.id", ondelete="CASCADE"), nullable=False),
        sa.Column("gps_lat", sa.Numeric(9, 6), nullable=True),
        sa.Column("gps_lng", sa.Numeric(9, 6), nullable=True),
    )
    op.create_index("idx_topo_nodes_pon", "topo_nodes", ["pon_id"]) 
    op.create_index("idx_topo_nodes_code", "topo_nodes", ["code"]) 

    op.create_table(
        "topo_edges",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("a_id", sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey("topo_nodes.id", ondelete="CASCADE"), nullable=False),
        sa.Column("b_id", sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey("topo_nodes.id", ondelete="CASCADE"), nullable=False),
        sa.Column("cable_code", sa.String(), nullable=True),
        sa.Column("length_m", sa.Numeric(), nullable=True),
    )
    op.create_index("idx_topo_edges_a", "topo_edges", ["a_id"]) 
    op.create_index("idx_topo_edges_b", "topo_edges", ["b_id"]) 
    op.create_index("idx_topo_edges_cable", "topo_edges", ["cable_code"]) 


def downgrade():
    op.drop_index("idx_topo_edges_cable", table_name="topo_edges")
    op.drop_index("idx_topo_edges_b", table_name="topo_edges")
    op.drop_index("idx_topo_edges_a", table_name="topo_edges")
    op.drop_table("topo_edges")

    op.drop_index("idx_topo_nodes_code", table_name="topo_nodes")
    op.drop_index("idx_topo_nodes_pon", table_name="topo_nodes")
    op.drop_table("topo_nodes")

