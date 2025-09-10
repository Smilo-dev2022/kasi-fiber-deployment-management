from alembic import op
import sqlalchemy as sa


revision = "0009_access_orgs_contracts_assignments_topology_incidents"
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
        sa.Column("type", sa.String(), nullable=False),  # MainContractor|Civil|Technical|Maintenance|Sales
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("idx_organizations_tenant_name", "organizations", ["tenant_id", "name"], unique=True)

    # Contracts
    op.create_table(
        "contracts",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("org_id", sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("scope", sa.String(), nullable=False),  # Civil|Technical|Maintenance|Sales
        sa.Column("wards", sa.Text(), nullable=True),  # comma separated ward codes
        sa.Column("sla_p1_minutes", sa.Integer(), nullable=True),
        sa.Column("sla_p2_minutes", sa.Integer(), nullable=True),
        sa.Column("sla_p3_minutes", sa.Integer(), nullable=True),
        sa.Column("sla_p4_minutes", sa.Integer(), nullable=True),
        sa.Column("rate_card_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=True),  # optional link to rate_cards if present
        sa.Column("valid_from", sa.Date(), nullable=True),
        sa.Column("valid_to", sa.Date(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("idx_contracts_org_scope", "contracts", ["org_id", "scope"]) 

    # Assignments (by PON or Ward) for step types
    op.create_table(
        "assignments",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("org_id", sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("step_type", sa.String(), nullable=False),  # Civil|Technical|Maintenance|Sales
        sa.Column("pon_id", sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey("pons.id", ondelete="CASCADE"), nullable=True),
        sa.Column("ward", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("idx_assignments_org_step", "assignments", ["org_id", "step_type"]) 
    op.create_index("uix_assignments_pon_step", "assignments", ["step_type", "pon_id"], unique=True, postgresql_where=sa.text("pon_id is not null"))
    op.create_index("uix_assignments_ward_step", "assignments", ["step_type", "ward"], unique=True, postgresql_where=sa.text("ward is not null"))

    # Splitters
    op.create_table(
        "splitters",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("pon_id", sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey("pons.id", ondelete="CASCADE"), nullable=False),
        sa.Column("closure_id", sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey("splice_closures.id", ondelete="SET NULL"), nullable=True),
        sa.Column("code", sa.String(), nullable=False, unique=True),
        sa.Column("ratio", sa.String(), nullable=True),  # e.g. 1:16, 1:8
        sa.Column("gps_lat", sa.Numeric(9, 6), nullable=True),
        sa.Column("gps_lng", sa.Numeric(9, 6), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("idx_splitters_pon", "splitters", ["pon_id"]) 

    # OLT ports map
    op.create_table(
        "olt_ports",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("device_id", sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey("devices.id", ondelete="CASCADE"), nullable=False),
        sa.Column("port", sa.String(), nullable=False),
        sa.Column("pon_id", sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey("pons.id", ondelete="SET NULL"), nullable=True),
        sa.Column("splitter_id", sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey("splitters.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("uix_olt_device_port", "olt_ports", ["device_id", "port"], unique=True)

    # Extend incidents
    op.add_column("incidents", sa.Column("assigned_org_id", sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey("organizations.id", ondelete="SET NULL"), nullable=True))
    op.add_column("incidents", sa.Column("severity_sla_minutes", sa.Integer(), nullable=True))
    op.add_column("incidents", sa.Column("due_at", sa.DateTime(timezone=True), nullable=True))
    op.create_index("idx_incidents_due", "incidents", ["due_at"]) 

    # Incident audit log
    op.create_table(
        "incident_audits",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("incident_id", sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey("incidents.id", ondelete="CASCADE"), nullable=False),
        sa.Column("action", sa.String(), nullable=False),  # assign|status|update
        sa.Column("from_org_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("to_org_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("by_role", sa.String(), nullable=True),
        sa.Column("by_org_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("idx_incident_audits_incident", "incident_audits", ["incident_id"]) 

    # Extend PON with ward for ward-based assignment
    op.add_column("pons", sa.Column("ward", sa.String(), nullable=True))
    op.create_index("idx_pons_ward", "pons", ["ward"]) 

    # OTDR events store for snapping
    op.create_table(
        "otdr_events",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("otdr_result_id", sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey("otdr_results.id", ondelete="CASCADE"), nullable=False),
        sa.Column("distance_m", sa.Numeric(10, 2), nullable=False),
        sa.Column("event_type", sa.String(), nullable=True),
        sa.Column("loss_db", sa.Numeric(6, 2), nullable=True),
        sa.Column("gps_lat", sa.Numeric(9, 6), nullable=True),
        sa.Column("gps_lng", sa.Numeric(9, 6), nullable=True),
        sa.Column("snap_closure_id", sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey("splice_closures.id", ondelete="SET NULL"), nullable=True),
        sa.Column("snap_segment_id", sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey("trench_segments.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("idx_otdr_events_result", "otdr_events", ["otdr_result_id"]) 


def downgrade():
    op.drop_index("idx_otdr_events_result", table_name="otdr_events")
    op.drop_table("otdr_events")

    op.drop_index("idx_pons_ward", table_name="pons")
    op.drop_column("pons", "ward")

    op.drop_index("idx_incident_audits_incident", table_name="incident_audits")
    op.drop_table("incident_audits")

    op.drop_index("idx_incidents_due", table_name="incidents")
    op.drop_column("incidents", "due_at")
    op.drop_column("incidents", "severity_sla_minutes")
    op.drop_column("incidents", "assigned_org_id")

    op.drop_index("uix_olt_device_port", table_name="olt_ports")
    op.drop_table("olt_ports")

    op.drop_index("idx_splitters_pon", table_name="splitters")
    op.drop_table("splitters")

    op.drop_index("uix_assignments_ward_step", table_name="assignments")
    op.drop_index("uix_assignments_pon_step", table_name="assignments")
    op.drop_index("idx_assignments_org_step", table_name="assignments")
    op.drop_table("assignments")

    op.drop_index("idx_contracts_org_scope", table_name="contracts")
    op.drop_table("contracts")

    op.drop_index("idx_organizations_tenant_name", table_name="organizations")
    op.drop_table("organizations")

