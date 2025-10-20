"""add ven_acks table

Revision ID: 202510200001
Revises: 202408051500
Create Date: 2025-10-20 00:01:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '202510200001'
down_revision: Union[str, None] = '202408051500'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create ven_acks table
    op.create_table(
        'ven_acks',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('ven_id', sa.String(length=255), nullable=False),
        sa.Column('event_id', sa.String(length=255), nullable=False),
        sa.Column('correlation_id', sa.String(length=255), nullable=True),
        sa.Column('op', sa.String(length=50), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.Column('requested_shed_kw', sa.Float(), nullable=True),
        sa.Column('actual_shed_kw', sa.Float(), nullable=True),
        sa.Column('circuits_curtailed', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('raw_payload', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for common queries
    op.create_index('ix_ven_acks_ven_id', 'ven_acks', ['ven_id'])
    op.create_index('ix_ven_acks_event_id', 'ven_acks', ['event_id'])
    op.create_index('ix_ven_acks_correlation_id', 'ven_acks', ['correlation_id'])
    op.create_index('ix_ven_acks_timestamp', 'ven_acks', ['timestamp'])


def downgrade() -> None:
    op.drop_index('ix_ven_acks_timestamp', table_name='ven_acks')
    op.drop_index('ix_ven_acks_correlation_id', table_name='ven_acks')
    op.drop_index('ix_ven_acks_event_id', table_name='ven_acks')
    op.drop_index('ix_ven_acks_ven_id', table_name='ven_acks')
    op.drop_table('ven_acks')
