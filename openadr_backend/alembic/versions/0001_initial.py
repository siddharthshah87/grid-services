"""initial tables"""

from alembic import op
import sqlalchemy as sa

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "vens",
        sa.Column("ven_id", sa.String(), primary_key=True),
        sa.Column("registration_id", sa.String(), unique=True),
        sa.Column("status", sa.String(), server_default="active"),
        sa.Column("created_at", sa.DateTime()),
    )
    op.create_table(
        "events",
        sa.Column("event_id", sa.String(), primary_key=True),
        sa.Column("ven_id", sa.String()),
        sa.Column("signal_name", sa.String()),
        sa.Column("signal_type", sa.String()),
        sa.Column("signal_payload", sa.String()),
        sa.Column("start_time", sa.DateTime()),
        sa.Column("response_required", sa.String()),
        sa.Column("raw", sa.JSON()),
        sa.Column("created_at", sa.DateTime()),
    )
    op.create_table(
        "devices",
        sa.Column("device_id", sa.String(), primary_key=True),
        sa.Column("ven_id", sa.String()),
        sa.Column("name", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime()),
    )
    op.create_table(
        "circuits",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(), unique=True),
        sa.Column("description", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime()),
    )
    op.create_table(
        "usage_records",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("device_id", sa.String(), sa.ForeignKey("devices.device_id")),
        sa.Column("circuit_id", sa.Integer(), sa.ForeignKey("circuits.id"), nullable=True),
        sa.Column("timestamp", sa.DateTime()),
        sa.Column("consumption", sa.Float()),
        sa.Column("created_at", sa.DateTime()),
    )


def downgrade() -> None:
    op.drop_table("usage_records")
    op.drop_table("circuits")
    op.drop_table("devices")
    op.drop_table("events")
    op.drop_table("vens")
