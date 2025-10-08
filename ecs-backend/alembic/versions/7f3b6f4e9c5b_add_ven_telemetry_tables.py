"""add ven telemetry tables

Revision ID: 7f3b6f4e9c5b
Revises: c476bf48d7ac
Create Date: 2025-08-02 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "7f3b6f4e9c5b"
down_revision: Union[str, Sequence[str], None] = "c476bf48d7ac"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create telemetry tables."""
    op.create_table(
        "ven_telemetry",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("ven_id", sa.String(), nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("used_power_kw", sa.Float(), nullable=False),
        sa.Column("shed_power_kw", sa.Float(), nullable=False, server_default=sa.text("0")),
        sa.Column("payload", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["ven_id"], ["vens.ven_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_ven_telemetry_ven_id", "ven_telemetry", ["ven_id"], unique=False)
    op.create_index("ix_ven_telemetry_timestamp", "ven_telemetry", ["timestamp"], unique=False)
    op.create_index(
        "ix_ven_telemetry_ven_timestamp",
        "ven_telemetry",
        ["ven_id", "timestamp"],
        unique=False,
    )

    op.create_table(
        "ven_load_samples",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("ven_id", sa.String(), nullable=False),
        sa.Column("load_id", sa.String(), nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("load_type", sa.String(), nullable=True),
        sa.Column("used_power_kw", sa.Float(), nullable=False),
        sa.Column("shed_power_kw", sa.Float(), nullable=False, server_default=sa.text("0")),
        sa.Column("capacity_kw", sa.Float(), nullable=True),
        sa.Column("shed_capability_kw", sa.Float(), nullable=True),
        sa.Column("payload", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["ven_id"], ["vens.ven_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_ven_load_samples_ven_id", "ven_load_samples", ["ven_id"], unique=False)
    op.create_index("ix_ven_load_samples_timestamp", "ven_load_samples", ["timestamp"], unique=False)
    op.create_index(
        "ix_ven_load_samples_ven_load_timestamp",
        "ven_load_samples",
        ["ven_id", "load_id", "timestamp"],
        unique=False,
    )

    op.create_table(
        "ven_statuses",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("ven_id", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("recorded_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("details", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["ven_id"], ["vens.ven_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_ven_statuses_ven_id", "ven_statuses", ["ven_id"], unique=False)
    op.create_index("ix_ven_statuses_recorded_at", "ven_statuses", ["recorded_at"], unique=False)
    op.create_index(
        "ix_ven_statuses_ven_recorded",
        "ven_statuses",
        ["ven_id", "recorded_at"],
        unique=False,
    )


def downgrade() -> None:
    """Drop telemetry tables."""
    op.drop_index("ix_ven_statuses_ven_recorded", table_name="ven_statuses")
    op.drop_index("ix_ven_statuses_recorded_at", table_name="ven_statuses")
    op.drop_index("ix_ven_statuses_ven_id", table_name="ven_statuses")
    op.drop_table("ven_statuses")

    op.drop_index("ix_ven_load_samples_ven_load_timestamp", table_name="ven_load_samples")
    op.drop_index("ix_ven_load_samples_timestamp", table_name="ven_load_samples")
    op.drop_index("ix_ven_load_samples_ven_id", table_name="ven_load_samples")
    op.drop_table("ven_load_samples")

    op.drop_index("ix_ven_telemetry_ven_timestamp", table_name="ven_telemetry")
    op.drop_index("ix_ven_telemetry_timestamp", table_name="ven_telemetry")
    op.drop_index("ix_ven_telemetry_ven_id", table_name="ven_telemetry")
    op.drop_table("ven_telemetry")
