"""Add VEN telemetry tables and enrich VEN/Event schema."""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "202408051500"
down_revision: Union[str, Sequence[str], None] = "202408021200"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Extend VEN table with metadata fields
    op.add_column("vens", sa.Column("name", sa.String(), nullable=True))
    op.add_column("vens", sa.Column("latitude", sa.Float(), nullable=True))
    op.add_column("vens", sa.Column("longitude", sa.Float(), nullable=True))

    # Extend events table with status/end/requested columns
    op.add_column(
        "events",
        sa.Column("status", sa.String(), nullable=False, server_default="scheduled"),
    )
    op.add_column("events", sa.Column("end_time", sa.DateTime(timezone=True), nullable=True))
    op.add_column(
        "events",
        sa.Column("requested_reduction_kw", sa.Float(), nullable=True),
    )

    # Drop legacy telemetry tables if present
    with op.batch_alter_table("telemetry_loads", schema=None) as batch_op:
        batch_op.drop_index("ix_telemetry_loads_load_id")
        batch_op.drop_index("ix_telemetry_loads_telemetry_id")
    op.drop_table("telemetry_loads")

    with op.batch_alter_table("telemetry_readings", schema=None) as batch_op:
        batch_op.drop_index("ix_telemetry_readings_timestamp")
        batch_op.drop_index("ix_telemetry_readings_ven_id")
    op.drop_table("telemetry_readings")

    # Create new telemetry tables
    op.create_table(
        "ven_telemetry",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("ven_id", sa.String(), sa.ForeignKey("vens.ven_id", ondelete="CASCADE"), nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("used_power_kw", sa.Float(), nullable=True),
        sa.Column("shed_power_kw", sa.Float(), nullable=True),
        sa.Column("requested_reduction_kw", sa.Float(), nullable=True),
        sa.Column("event_id", sa.String(), sa.ForeignKey("events.event_id", ondelete="SET NULL"), nullable=True),
        sa.Column("battery_soc", sa.Float(), nullable=True),
        sa.Column("raw_payload", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index(op.f("ix_ven_telemetry_ven_id"), "ven_telemetry", ["ven_id"], unique=False)
    op.create_index(op.f("ix_ven_telemetry_timestamp"), "ven_telemetry", ["timestamp"], unique=False)
    op.create_index(op.f("ix_ven_telemetry_event_id"), "ven_telemetry", ["event_id"], unique=False)

    op.create_table(
        "ven_load_samples",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("telemetry_id", sa.Integer(), sa.ForeignKey("ven_telemetry.id", ondelete="CASCADE"), nullable=False),
        sa.Column("load_id", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=True),
        sa.Column("type", sa.String(), nullable=True),
        sa.Column("capacity_kw", sa.Float(), nullable=True),
        sa.Column("current_power_kw", sa.Float(), nullable=True),
        sa.Column("shed_capability_kw", sa.Float(), nullable=True),
        sa.Column("enabled", sa.Boolean(), nullable=True),
        sa.Column("priority", sa.Integer(), nullable=True),
        sa.Column("raw_payload", sa.JSON(), nullable=True),
    )
    op.create_index(op.f("ix_ven_load_samples_telemetry_id"), "ven_load_samples", ["telemetry_id"], unique=False)

    op.create_table(
        "ven_status",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("ven_id", sa.String(), sa.ForeignKey("vens.ven_id", ondelete="CASCADE"), nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("current_power_kw", sa.Float(), nullable=True),
        sa.Column("shed_availability_kw", sa.Float(), nullable=True),
        sa.Column("active_event_id", sa.String(), sa.ForeignKey("events.event_id", ondelete="SET NULL"), nullable=True),
        sa.Column("raw_payload", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index(op.f("ix_ven_status_ven_id"), "ven_status", ["ven_id"], unique=False)
    op.create_index(op.f("ix_ven_status_timestamp"), "ven_status", ["timestamp"], unique=False)

    # Ensure new columns are nullable defaults applied to existing rows
    with op.batch_alter_table("events", schema=None) as batch_op:
        batch_op.alter_column("status", server_default=None)


def downgrade() -> None:
    with op.batch_alter_table("events", schema=None) as batch_op:
        batch_op.drop_column("requested_reduction_kw")
        batch_op.drop_column("end_time")
        batch_op.drop_column("status")

    with op.batch_alter_table("vens", schema=None) as batch_op:
        batch_op.drop_column("longitude")
        batch_op.drop_column("latitude")
        batch_op.drop_column("name")

    op.drop_index(op.f("ix_ven_status_timestamp"), table_name="ven_status")
    op.drop_index(op.f("ix_ven_status_ven_id"), table_name="ven_status")
    op.drop_table("ven_status")

    op.drop_index(op.f("ix_ven_load_samples_telemetry_id"), table_name="ven_load_samples")
    op.drop_table("ven_load_samples")

    op.drop_index(op.f("ix_ven_telemetry_event_id"), table_name="ven_telemetry")
    op.drop_index(op.f("ix_ven_telemetry_timestamp"), table_name="ven_telemetry")
    op.drop_index(op.f("ix_ven_telemetry_ven_id"), table_name="ven_telemetry")
    op.drop_table("ven_telemetry")

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
    op.create_index(op.f("ix_telemetry_readings_ven_id"), "telemetry_readings", ["ven_id"], unique=False)
    op.create_index(op.f("ix_telemetry_readings_timestamp"), "telemetry_readings", ["timestamp"], unique=False)

    op.create_table(
        "telemetry_loads",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("telemetry_id", sa.Integer(), sa.ForeignKey("telemetry_readings.id", ondelete="CASCADE"), nullable=False),
        sa.Column("load_id", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=True),
        sa.Column("type", sa.String(), nullable=True),
        sa.Column("capacity_kw", sa.Float(), nullable=True),
        sa.Column("current_power_kw", sa.Float(), nullable=True),
        sa.Column("shed_capability_kw", sa.Float(), nullable=True),
        sa.Column("enabled", sa.Boolean(), nullable=True),
        sa.Column("priority", sa.Integer(), nullable=True),
        sa.Column("raw_payload", sa.JSON(), nullable=True),
    )
    op.create_index(op.f("ix_telemetry_loads_telemetry_id"), "telemetry_loads", ["telemetry_id"], unique=False)
    op.create_index(op.f("ix_telemetry_loads_load_id"), "telemetry_loads", ["load_id"], unique=False)
