"""add ven heartbeat tracking

Revision ID: 202510210001
Revises: 202510200001
Create Date: 2025-10-21 06:30:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '202510210001'
down_revision = '202510200001'
branch_labels = None
depends_on = None


def upgrade():
    # Add last_heartbeat column to vens table
    op.add_column('vens', sa.Column('last_heartbeat', sa.DateTime(timezone=True), nullable=True))
    
    # Create index for efficient offline detection queries
    op.create_index('idx_vens_last_heartbeat', 'vens', ['last_heartbeat'])


def downgrade():
    op.drop_index('idx_vens_last_heartbeat', table_name='vens')
    op.drop_column('vens', 'last_heartbeat')
