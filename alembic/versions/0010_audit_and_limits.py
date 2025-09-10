from alembic import op
import sqlalchemy as sa


revision = '0010_audit_and_limits'
down_revision = '0009_access_ops'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'audit_events',
        sa.Column('id', sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('entity_type', sa.String(), nullable=False),
        sa.Column('entity_id', sa.dialects.postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('action', sa.String(), nullable=False),
        sa.Column('at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('by', sa.String(), nullable=True),
        sa.Column('before', sa.JSON(), nullable=True),
        sa.Column('after', sa.JSON(), nullable=True),
    )
    op.create_index('idx_audit_entity', 'audit_events', ['entity_type', 'entity_id'])


def downgrade():
    op.drop_index('idx_audit_entity', table_name='audit_events')
    op.drop_table('audit_events')

