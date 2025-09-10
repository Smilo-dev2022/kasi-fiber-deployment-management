from alembic import op
import sqlalchemy as sa


revision = "0009_access_ops"
down_revision = "0008_fiber_technical"
branch_labels = None
depends_on = None


def upgrade():
    # Organizations
    op.create_table(
        "organizations",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("type", sa.String(), nullable=False),  # Civil, Technical, Maintenance, Sales
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("idx_orgs_type", "organizations", ["type"]) 

    # Contracts
    op.create_table(
        "contracts",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("org_id", sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey("organizations.id", ondelete="CASCADE")),
        sa.Column("scope_type", sa.String(), nullable=False),  # Civil, Technical, Maintenance, Sales
        sa.Column("wards", sa.ARRAY(sa.String()), nullable=True),
        sa.Column("sla_p1_min", sa.Integer(), nullable=True),
        sa.Column("sla_p2_min", sa.Integer(), nullable=True),
        sa.Column("sla_p3_min", sa.Integer(), nullable=True),
        sa.Column("sla_p4_min", sa.Integer(), nullable=True),
        sa.Column("rate_card_ref", sa.String(), nullable=True),
        sa.Column("active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("valid_from", sa.Date(), nullable=True),
        sa.Column("valid_to", sa.Date(), nullable=True),
    )
    op.create_index("idx_contracts_org", "contracts", ["org_id"]) 
    op.create_index("idx_contracts_scope", "contracts", ["scope_type"]) 

    # Assignments: maps PON or ward to org for a step type
    op.create_table(
        "assignments",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("org_id", sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey("organizations.id", ondelete="CASCADE")),
        sa.Column("pon_id", sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey("pons.id", ondelete="CASCADE"), nullable=True),
        sa.Column("ward", sa.String(), nullable=True),
        sa.Column("step_type", sa.String(), nullable=False),  # build step or task type
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("idx_assignments_org", "assignments", ["org_id"]) 
    op.create_index("idx_assignments_pon", "assignments", ["pon_id"]) 
    op.create_index("idx_assignments_step", "assignments", ["step_type"]) 

    # Splitters and port map
    op.create_table(
        "splitters",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("pon_id", sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey("pons.id", ondelete="CASCADE")),
        sa.Column("closure_id", sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey("splice_closures.id", ondelete="SET NULL"), nullable=True),
        sa.Column("code", sa.String(), nullable=False, unique=True),
        sa.Column("ratio", sa.String(), nullable=True),  # 1:8, 1:16, 1:32, 1:64
        sa.Column("gps_lat", sa.Numeric(9, 6), nullable=True),
        sa.Column("gps_lng", sa.Numeric(9, 6), nullable=True),
        sa.Column("status", sa.String(), server_default=sa.text("'Planned'"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("idx_splitters_pon", "splitters", ["pon_id"]) 

    op.create_table(
        "port_map",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("pon_id", sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey("pons.id", ondelete="CASCADE")),
        sa.Column("olt_device_id", sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey("devices.id", ondelete="SET NULL"), nullable=True),
        sa.Column("olt_port", sa.String(), nullable=True),
        sa.Column("splitter_id", sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey("splitters.id", ondelete="SET NULL"), nullable=True),
        sa.Column("branch_no", sa.Integer(), nullable=True),
        sa.Column("onu_device_id", sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey("devices.id", ondelete="SET NULL"), nullable=True),
        sa.Column("drop_code", sa.String(), nullable=True),
    )
    op.create_index("idx_port_map_pon", "port_map", ["pon_id"]) 
    op.create_index("idx_port_map_olt", "port_map", ["olt_device_id", "olt_port"]) 

    # Cable register for polylines and chainage
    op.create_table(
        "cable_register",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("pon_id", sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey("pons.id", ondelete="CASCADE")),
        sa.Column("cable_code", sa.String(), nullable=False),
        sa.Column("polyline", sa.Text(), nullable=True),  # JSON encoded [ [lat, lng], ... ]
        sa.Column("length_m", sa.Numeric(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("idx_cable_register_pon", "cable_register", ["pon_id"]) 
    op.create_index("idx_cable_register_code", "cable_register", ["cable_code"], unique=False) 

    # OTDR events derived from results with snapped GPS
    op.create_table(
        "otdr_events",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("otdr_result_id", sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey("otdr_results.id", ondelete="CASCADE")),
        sa.Column("distance_m", sa.Numeric(8, 2), nullable=False),
        sa.Column("gps_lat", sa.Numeric(9, 6), nullable=True),
        sa.Column("gps_lng", sa.Numeric(9, 6), nullable=True),
        sa.Column("nearest_closure_id", sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey("splice_closures.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("idx_otdr_events_result", "otdr_events", ["otdr_result_id"]) 

    # Extend incidents with assignment and SLA due
    op.add_column("incidents", sa.Column("assigned_org_id", sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey("organizations.id", ondelete="SET NULL"), nullable=True))
    op.add_column("incidents", sa.Column("severity_sla_minutes", sa.Integer(), nullable=True))
    op.add_column("incidents", sa.Column("due_at", sa.DateTime(timezone=True), nullable=True))
    op.create_index("idx_incidents_assigned_org", "incidents", ["assigned_org_id"]) 

    # Optional: enable RLS scaffolding on key tables (no policies defined here)
    op.execute("ALTER TABLE organizations ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE contracts ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE assignments ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE incidents ENABLE ROW LEVEL SECURITY")


def downgrade():
    op.drop_index("idx_incidents_assigned_org", table_name="incidents")
    op.drop_column("incidents", "due_at")
    op.drop_column("incidents", "severity_sla_minutes")
    op.drop_column("incidents", "assigned_org_id")

    op.drop_index("idx_otdr_events_result", table_name="otdr_events")
    op.drop_table("otdr_events")

    op.drop_index("idx_cable_register_code", table_name="cable_register")
    op.drop_index("idx_cable_register_pon", table_name="cable_register")
    op.drop_table("cable_register")

    op.drop_index("idx_port_map_olt", table_name="port_map")
    op.drop_index("idx_port_map_pon", table_name="port_map")
    op.drop_table("port_map")

    op.drop_index("idx_splitters_pon", table_name="splitters")
    op.drop_table("splitters")

    op.drop_index("idx_assignments_step", table_name="assignments")
    op.drop_index("idx_assignments_pon", table_name="assignments")
    op.drop_index("idx_assignments_org", table_name="assignments")
    op.drop_table("assignments")

    op.drop_index("idx_contracts_scope", table_name="contracts")
    op.drop_index("idx_contracts_org", table_name="contracts")
    op.drop_table("contracts")

    op.drop_index("idx_orgs_type", table_name="organizations")
    op.drop_table("organizations")

