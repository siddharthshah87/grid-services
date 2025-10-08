"""Create tables to store telemetry and load snapshots.

Revision ID: 202408021200
Revises: c476bf48d7ac
Create Date: 2024-08-02 12:00:00
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "202408021200"
down_revision: Union[str, Sequence[str], None] = "c476bf48d7ac"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "telemetry_readings",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("ven_id", sa.String(), nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("used_power_kw", sa.Float(), nullable=True),
        sa.Column("shed_power_kw", sa.Float(), nullable=True),
        sa.Column("requested_reduction_kw", sa.Float(), nullable=True),
        sa.Column("event_id", sa.String(), nullable=True),
        sa.Column("battery_soc", sa.Float(), nullable=True),
        sa.Column("raw_payload", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )
    op.create_index(
        op.f("ix_telemetry_readings_ven_id"),
        "telemetry_readings",
        ["ven_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_telemetry_readings_timestamp"),
        "telemetry_readings",
        ["timestamp"],
        unique=False,
    )

    op.create_table(
        "telemetry_loads",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("telemetry_id", sa.Integer(), nullable=False),
        sa.Column("load_id", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=True),
        sa.Column("type", sa.String(), nullable=True),
        sa.Column("capacity_kw", sa.Float(), nullable=True),
        sa.Column("current_power_kw", sa.Float(), nullable=True),
        sa.Column("shed_capability_kw", sa.Float(), nullable=True),
        sa.Column("enabled", sa.Boolean(), nullable=True),
        sa.Column("priority", sa.Integer(), nullable=True),
        sa.Column("raw_payload", sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint([
            "telemetry_id"
        ], ["telemetry_readings.id"], ondelete="CASCADE"),
    )
    op.create_index(
        op.f("ix_telemetry_loads_telemetry_id"),
        "telemetry_loads",
        ["telemetry_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_telemetry_loads_load_id"),
        "telemetry_loads",
        ["load_id"],
        unique=False,
    )

    op.create_table(
        "load_snapshots",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("ven_id", sa.String(), nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("load_id", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=True),
        sa.Column("type", sa.String(), nullable=True),
        sa.Column("capacity_kw", sa.Float(), nullable=True),
        sa.Column("current_power_kw", sa.Float(), nullable=True),
        sa.Column("shed_capability_kw", sa.Float(), nullable=True),
        sa.Column("enabled", sa.Boolean(), nullable=True),
        sa.Column("priority", sa.Integer(), nullable=True),
        sa.Column("raw_payload", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )
    op.create_index(op.f("ix_load_snapshots_ven_id"), "load_snapshots", ["ven_id"], unique=False)
    op.create_index(
        op.f("ix_load_snapshots_timestamp"),
        "load_snapshots",
        ["timestamp"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_load_snapshots_timestamp"), table_name="load_snapshots")
    op.drop_index(op.f("ix_load_snapshots_ven_id"), table_name="load_snapshots")
    op.drop_table("load_snapshots")

    op.drop_index(op.f("ix_telemetry_loads_load_id"), table_name="telemetry_loads")
    op.drop_index(op.f("ix_telemetry_loads_telemetry_id"), table_name="telemetry_loads")
    op.drop_table("telemetry_loads")

    op.drop_index(op.f("ix_telemetry_readings_timestamp"), table_name="telemetry_readings")
    op.drop_index(op.f("ix_telemetry_readings_ven_id"), table_name="telemetry_readings")
    op.drop_table("telemetry_readings")
