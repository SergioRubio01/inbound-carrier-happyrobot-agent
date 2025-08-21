"""Remove negotiations table and infrastructure

Revision ID: 005_remove_negotiations_table
Revises: 909554643437
Create Date: 2025-08-21 10:30:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "005_remove_negotiations_table"
down_revision: Union[str, None] = "909554643437"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Drop negotiations table completely."""
    # Drop the negotiations table if it exists (CASCADE will drop all foreign keys and indexes)
    op.execute("DROP TABLE IF EXISTS negotiations CASCADE")


def downgrade() -> None:
    """Recreate negotiations table based on original schema."""
    # Recreate negotiations table (based on original schema from 001_initial_schema.py)
    op.create_table(
        "negotiations",
        sa.Column("negotiation_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("call_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("load_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("carrier_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("mc_number", sa.String(length=20), nullable=True),
        sa.Column("session_id", sa.String(length=100), nullable=False),
        sa.Column("session_start", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("session_end", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=True),
        sa.Column("round_number", sa.Integer(), nullable=False),
        sa.Column("max_rounds", sa.Integer(), nullable=True),
        sa.Column("carrier_offer", sa.NUMERIC(precision=10, scale=2), nullable=False),
        sa.Column("system_response", sa.String(length=50), nullable=False),
        sa.Column("counter_offer", sa.NUMERIC(precision=10, scale=2), nullable=True),
        sa.Column("loadboard_rate", sa.NUMERIC(precision=10, scale=2), nullable=False),
        sa.Column(
            "minimum_acceptable", sa.NUMERIC(precision=10, scale=2), nullable=True
        ),
        sa.Column(
            "maximum_acceptable", sa.NUMERIC(precision=10, scale=2), nullable=True
        ),
        sa.Column("decision_factors", postgresql.JSONB(), nullable=True),
        sa.Column("message_to_carrier", sa.Text(), nullable=True),
        sa.Column("justification", sa.Text(), nullable=True),
        sa.Column("final_status", sa.String(length=30), nullable=True),
        sa.Column("agreed_rate", sa.NUMERIC(precision=10, scale=2), nullable=True),
        sa.Column("response_time_seconds", sa.Integer(), nullable=True),
        sa.Column("total_duration_seconds", sa.Integer(), nullable=True),
        sa.Column("created_by", sa.String(length=100), nullable=True),
        sa.Column("version", sa.Integer(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["call_id"],
            ["calls.call_id"],
        ),
        sa.ForeignKeyConstraint(
            ["carrier_id"],
            ["carriers.carrier_id"],
        ),
        sa.ForeignKeyConstraint(
            ["load_id"],
            ["loads.load_id"],
        ),
        sa.PrimaryKeyConstraint("negotiation_id"),
    )

    # Recreate indexes for negotiations table
    op.create_index(
        op.f("ix_negotiations_call_id"), "negotiations", ["call_id"], unique=False
    )
    op.create_index(
        op.f("ix_negotiations_load_id"), "negotiations", ["load_id"], unique=False
    )
    op.create_index(
        op.f("ix_negotiations_carrier_id"), "negotiations", ["carrier_id"], unique=False
    )
    op.create_index(
        op.f("ix_negotiations_session_id"), "negotiations", ["session_id"], unique=False
    )
    op.create_index(
        op.f("ix_negotiations_is_active"), "negotiations", ["is_active"], unique=False
    )
    op.create_index(
        op.f("ix_negotiations_round_number"),
        "negotiations",
        ["round_number"],
        unique=False,
    )
    op.create_index(
        op.f("ix_negotiations_final_status"),
        "negotiations",
        ["final_status"],
        unique=False,
    )
