from alembic import op
import sqlalchemy as sa


revision = "0009_access_and_topology"
down_revision = "0008_fiber_technical"
branch_labels = None
depends_on = None


def upgrade():
    # Organizations
    op.create_table(
        "organizations",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", sa.dialects.postgresql.UUID(as_uuid=True)),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("org_type", sa.String(), nullable=False),  # Civil, Technical, Maintenance, Sales
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("idx_orgs_type", "organizations", ["org_type"])

    # Wards
    op.create_table(
        "wards",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", sa.dialects.postgresql.UUID(as_uuid=True)),
        sa.Column("name", sa.String(), nullable=False, unique=True),
    )

    # PONs: optional ward link
    with op.batch_alter_table("pons") as b:
        b.add_column(sa.Column("ward_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=True))
        b.create_foreign_key("fk_pons_ward", "wards", ["ward_id"], ["id"], ondelete="SET NULL")

    # Contracts
    op.create_table(
        "contracts",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", sa.dialects.postgresql.UUID(as_uuid=True)),
        sa.Column("org_id", sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey("organizations.id", ondelete="CASCADE")),
        sa.Column("scope", sa.String(), nullable=False),  # Civil, Technical, Maintenance, Sales
        sa.Column("wards", sa.ARRAY(sa.dialects.postgresql.UUID(as_uuid=True))),
        sa.Column("sla_minutes_p1", sa.Integer(), server_default="60", nullable=False),
        sa.Column("sla_minutes_p2", sa.Integer(), server_default="240", nullable=False),
        sa.Column("sla_minutes_p3", sa.Integer(), server_default="1440", nullable=False),
        sa.Column("sla_minutes_p4", sa.Integer(), server_default="4320", nullable=False),
        sa.Column("rate_card", sa.JSON(), nullable=True),  # optional embedded rate card per contract
        sa.Column("active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("idx_contracts_org", "contracts", ["org_id", "active"]) 

    # Assignments: ward or PON scoped, by step type
    op.create_table(
        "assignments",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", sa.dialects.postgresql.UUID(as_uuid=True)),
        sa.Column("org_id", sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("scope", sa.String(), nullable=False),  # Civil, Technical, Maintenance, Sales
        sa.Column("step_type", sa.String(), nullable=True),
        sa.Column("ward_id", sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey("wards.id", ondelete="SET NULL"), nullable=True),
        sa.Column("pon_id", sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey("pons.id", ondelete="CASCADE"), nullable=True),
        sa.Column("active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("idx_assignments_target", "assignments", ["org_id", "scope", "active"]) 
    op.create_index("idx_assignments_ward_step", "assignments", ["ward_id", "step_type"]) 
    op.create_index("idx_assignments_pon_step", "assignments", ["pon_id", "step_type"]) 

    # Incidents extension
    with op.batch_alter_table("incidents") as b:
        b.add_column(sa.Column("assigned_org_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=True))
        b.add_column(sa.Column("severity_sla_minutes", sa.Integer(), nullable=True))
        b.add_column(sa.Column("due_at", sa.DateTime(timezone=True), nullable=True))
        b.create_foreign_key("fk_incidents_assigned_org", "organizations", ["assigned_org_id"], ["id"], ondelete="SET NULL")

    # Incident audit trail
    op.create_table(
        "incident_audits",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("incident_id", sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey("incidents.id", ondelete="CASCADE")),
        sa.Column("action", sa.String(), nullable=False),  # assign, update_status, resolve, close
        sa.Column("actor_org_id", sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey("organizations.id", ondelete="SET NULL")),
        sa.Column("metadata", sa.JSON(), nullable=True),
        sa.Column("at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("idx_inc_aud_incident", "incident_audits", ["incident_id", "at"]) 

    # Topology: OLT ports, splitters, port map
    op.create_table(
        "olt_ports",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("device_id", sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey("devices.id", ondelete="CASCADE"), nullable=False),
        sa.Column("pon_id", sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey("pons.id", ondelete="SET NULL"), nullable=True),
        sa.Column("name", sa.String(), nullable=False),  # e.g., 1/1/1
        sa.Column("max_onu", sa.Integer(), nullable=True),
    )
    op.create_index("idx_olt_ports_device", "olt_ports", ["device_id"]) 

    op.create_table(
        "splitters",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("pon_id", sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey("pons.id", ondelete="CASCADE"), nullable=False),
        sa.Column("closure_id", sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey("splice_closures.id", ondelete="SET NULL"), nullable=True),
        sa.Column("code", sa.String(), nullable=False, unique=True),
        sa.Column("ratio", sa.String(), nullable=False),  # 1:8, 1:16, 1:32
        sa.Column("gps_lat", sa.Numeric(9, 6), nullable=True),
        sa.Column("gps_lng", sa.Numeric(9, 6), nullable=True),
    )
    op.create_index("idx_splitters_pon", "splitters", ["pon_id"]) 

    op.create_table(
        "port_maps",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("olt_port_id", sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey("olt_ports.id", ondelete="CASCADE"), nullable=False),
        sa.Column("splitter_id", sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey("splitters.id", ondelete="CASCADE"), nullable=False),
        sa.Column("splitter_port", sa.Integer(), nullable=True),
        sa.Column("onu_device_id", sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey("devices.id", ondelete="SET NULL"), nullable=True),
        sa.Column("drop_length_m", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("idx_port_maps_olt", "port_maps", ["olt_port_id"]) 
    op.create_index("idx_port_maps_splitter", "port_maps", ["splitter_id"]) 


def downgrade():
    op.drop_index("idx_port_maps_splitter", table_name="port_maps")
    op.drop_index("idx_port_maps_olt", table_name="port_maps")
    op.drop_table("port_maps")
    op.drop_index("idx_splitters_pon", table_name="splitters")
    op.drop_table("splitters")
    op.drop_index("idx_olt_ports_device", table_name="olt_ports")
    op.drop_table("olt_ports")
    op.drop_index("idx_inc_aud_incident", table_name="incident_audits")
    op.drop_table("incident_audits")
    with op.batch_alter_table("incidents") as b:
        b.drop_constraint("fk_incidents_assigned_org", type_="foreignkey")
        b.drop_column("due_at")
        b.drop_column("severity_sla_minutes")
        b.drop_column("assigned_org_id")
    op.drop_index("idx_assignments_pon_step", table_name="assignments")
    op.drop_index("idx_assignments_ward_step", table_name="assignments")
    op.drop_index("idx_assignments_target", table_name="assignments")
    op.drop_table("assignments")
    op.drop_index("idx_contracts_org", table_name="contracts")
    op.drop_table("contracts")
    with op.batch_alter_table("pons") as b:
        b.drop_constraint("fk_pons_ward", type_="foreignkey")
        b.drop_column("ward_id")
    op.drop_table("wards")
    op.drop_index("idx_orgs_type", table_name="organizations")
    op.drop_table("organizations")

