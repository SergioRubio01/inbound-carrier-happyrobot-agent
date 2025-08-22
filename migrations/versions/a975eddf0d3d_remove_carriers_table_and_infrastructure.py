"""Remove carriers table and infrastructure

Revision ID: a975eddf0d3d
Revises: remove_rate_add_sentiment
Create Date: 2025-08-22 15:00:31.168817

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "a975eddf0d3d"
down_revision: Union[str, None] = "remove_rate_add_sentiment"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Drop carriers table and all associated indexes."""
    # Drop the carriers table (CASCADE will drop dependent indexes)
    op.execute("DROP TABLE IF EXISTS carriers CASCADE")


def downgrade() -> None:
    """Recreate carriers table with original schema from 001_initial_schema.py."""
    # Recreate carriers table
    op.create_table(
        "carriers",
        sa.Column("carrier_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("mc_number", sa.String(length=20), nullable=False),
        sa.Column("dot_number", sa.String(length=20), nullable=True),
        sa.Column("legal_name", sa.String(length=255), nullable=False),
        sa.Column("dba_name", sa.String(length=255), nullable=True),
        sa.Column("entity_type", sa.String(length=50), nullable=False),
        sa.Column("operating_status", sa.String(length=50), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("insurance_on_file", sa.Boolean(), nullable=True),
        sa.Column("bipd_required", sa.NUMERIC(precision=12, scale=2), nullable=True),
        sa.Column("bipd_on_file", sa.NUMERIC(precision=12, scale=2), nullable=True),
        sa.Column("cargo_required", sa.NUMERIC(precision=12, scale=2), nullable=True),
        sa.Column("cargo_on_file", sa.NUMERIC(precision=12, scale=2), nullable=True),
        sa.Column("bond_required", sa.NUMERIC(precision=12, scale=2), nullable=True),
        sa.Column("bond_on_file", sa.NUMERIC(precision=12, scale=2), nullable=True),
        sa.Column("safety_rating", sa.String(length=20), nullable=True),
        sa.Column("safety_rating_date", sa.Date(), nullable=True),
        sa.Column("safety_scores", postgresql.JSONB(), nullable=True),
        sa.Column("primary_contact", postgresql.JSONB(), nullable=True),
        sa.Column("address", postgresql.JSONB(), nullable=True),
        sa.Column("eligibility_notes", sa.Text(), nullable=True),
        sa.Column("last_verified_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("verification_source", sa.String(length=50), nullable=True),
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
        sa.PrimaryKeyConstraint("carrier_id"),
    )

    # Recreate indexes
    op.create_index(
        op.f("ix_carriers_mc_number"), "carriers", ["mc_number"], unique=True
    )
    op.create_index(
        op.f("ix_carriers_dot_number"), "carriers", ["dot_number"], unique=False
    )
