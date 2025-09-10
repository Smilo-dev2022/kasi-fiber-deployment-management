from alembic import op
import sqlalchemy as sa


revision = "0009_orgs_contracts_assignments_topology"
down_revision = "0008_fiber_technical"
branch_labels = None
depends_on = None


def upgrade():
    # organizations
    op.create_table(
        "organizations",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("name", sa.String(), nullable=False, unique=True),
        sa.Column("type", sa.String(), nullable=False),  # Main, Civil, Technical, Maintenance, Sales
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("idx_orgs_type", "organizations", ["type"]) 

    # contracts
    op.create_table(
        "contracts",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("org_id", sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("scope", sa.String(), nullable=False),  # Civil, Technical, Maintenance, Sales
        sa.Column("sla_p1_minutes", sa.Integer(), nullable=True),
        sa.Column("sla_p2_minutes", sa.Integer(), nullable=True),
        sa.Column("sla_p3_minutes", sa.Integer(), nullable=True),
        sa.Column("sla_p4_minutes", sa.Integer(), nullable=True),
        sa.Column("valid_from", sa.Date(), nullable=False),
        sa.Column("valid_to", sa.Date(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("idx_contracts_org", "contracts", ["org_id"]) 
    op.create_index("idx_contracts_scope", "contracts", ["scope"]) 

    # contract_wards (optional ward scoping via code/text)
    op.create_table(
        "contract_wards",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("contract_id", sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey("contracts.id", ondelete="CASCADE"), nullable=False),
        sa.Column("ward_code", sa.String(), nullable=False),
    )
    op.create_index("idx_contract_wards_contract", "contract_wards", ["contract_id"]) 

    # assignments - map PON or ward to organization for step types
    op.create_table(
        "assignments",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("org_id", sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("step", sa.String(), nullable=False),  # Permissions, Trenching, Chambers, Reinstatement, Splicing, Maintenance, Sales
        sa.Column("pon_id", sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey("pons.id", ondelete="CASCADE"), nullable=True),
        sa.Column("ward_code", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("idx_assignments_org_step", "assignments", ["org_id", "step"]) 
    op.create_index("idx_assignments_pon", "assignments", ["pon_id"]) 

    # Extend incidents with assignment and SLA
    op.add_column("incidents", sa.Column("assigned_org_id", sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey("organizations.id", ondelete="SET NULL"), nullable=True))
    op.add_column("incidents", sa.Column("severity_sla_minutes", sa.Integer(), nullable=True))
    op.add_column("incidents", sa.Column("due_at", sa.DateTime(timezone=True), nullable=True))
    op.create_index("idx_incidents_assigned_org", "incidents", ["assigned_org_id"]) 

    # Topology additions: splitters and port maps, plus cable register for snapping
    op.create_table(
        "splitters",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("pon_id", sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey("pons.id", ondelete="CASCADE"), nullable=False),
        sa.Column("closure_id", sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey("splice_closures.id", ondelete="SET NULL"), nullable=True),
        sa.Column("code", sa.String(), nullable=False, unique=True),
        sa.Column("ratio", sa.Integer(), nullable=False),  # 2,4,8,16,32,64
        sa.Column("gps_lat", sa.Numeric(9, 6), nullable=True),
        sa.Column("gps_lng", sa.Numeric(9, 6), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("idx_splitters_pon", "splitters", ["pon_id"]) 

    op.create_table(
        "splitter_ports",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("splitter_id", sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey("splitters.id", ondelete="CASCADE"), nullable=False),
        sa.Column("port_no", sa.Integer(), nullable=False),
        sa.Column("tray_id", sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey("splice_trays.id", ondelete="SET NULL"), nullable=True),
        sa.Column("onu_device_id", sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey("devices.id", ondelete="SET NULL"), nullable=True),
    )
    op.create_index("idx_splitter_ports_splitter", "splitter_ports", ["splitter_id"]) 

    op.create_table(
        "olt_ports",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("pon_id", sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey("pons.id", ondelete="CASCADE"), nullable=False),
        sa.Column("device_id", sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey("devices.id", ondelete="CASCADE"), nullable=False),
        sa.Column("port", sa.String(), nullable=False),
        sa.Column("splitter_id", sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey("splitters.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("idx_olt_ports_device_port", "olt_ports", ["device_id", "port"]) 

    op.create_table(
        "cable_register",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("pon_id", sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey("pons.id", ondelete="CASCADE"), nullable=False),
        sa.Column("code", sa.String(), nullable=False, unique=True),
        sa.Column("type", sa.String(), nullable=False),  # feeder, distribution, drop
        sa.Column("polyline", sa.Text(), nullable=True),  # encoded or lat,lng;lat,lng
        sa.Column("length_m", sa.Numeric(12, 2), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("idx_cable_register_pon", "cable_register", ["pon_id"]) 


def downgrade():
    op.drop_index("idx_cable_register_pon", table_name="cable_register")
    op.drop_table("cable_register")

    op.drop_index("idx_olt_ports_device_port", table_name="olt_ports")
    op.drop_table("olt_ports")

    op.drop_index("idx_splitter_ports_splitter", table_name="splitter_ports")
    op.drop_table("splitter_ports")

    op.drop_index("idx_splitters_pon", table_name="splitters")
    op.drop_table("splitters")

    op.drop_index("idx_incidents_assigned_org", table_name="incidents")
    op.drop_column("incidents", "due_at")
    op.drop_column("incidents", "severity_sla_minutes")
    op.drop_column("incidents", "assigned_org_id")

    op.drop_index("idx_assignments_pon", table_name="assignments")
    op.drop_index("idx_assignments_org_step", table_name="assignments")
    op.drop_table("assignments")

    op.drop_index("idx_contract_wards_contract", table_name="contract_wards")
    op.drop_table("contract_wards")

    op.drop_index("idx_contracts_scope", table_name="contracts")
    op.drop_index("idx_contracts_org", table_name="contracts")
    op.drop_table("contracts")

    op.drop_index("idx_orgs_type", table_name="organizations")
    op.drop_table("organizations")

