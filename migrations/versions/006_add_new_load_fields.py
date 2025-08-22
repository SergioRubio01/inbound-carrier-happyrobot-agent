"""Add booked, session_id fields and update load fields

Revision ID: 006_add_new_load_fields
Revises: 8e55464365f8
Create Date: 2025-08-22 10:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "006_add_new_load_fields"
down_revision: Union[str, None] = "8e55464365f8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add booked column with default False
    op.add_column(
        "loads",
        sa.Column("booked", sa.Boolean(), nullable=False, server_default="false"),
    )

    # Add session_id column as nullable string
    op.add_column("loads", sa.Column("session_id", sa.String(255), nullable=True))

    # Add num_of_pieces column (pieces was removed in migration 004)
    op.add_column("loads", sa.Column("num_of_pieces", sa.Integer(), nullable=True))

    # Add dimensions column (was removed in migration 004)
    op.add_column("loads", sa.Column("dimensions", sa.String(255), nullable=True))

    # Add miles column as string (was removed in migration 004)
    op.add_column("loads", sa.Column("miles", sa.String(50), nullable=True))

    # Create index on booked field for performance
    op.create_index("ix_loads_booked", "loads", ["booked"])


def downgrade() -> None:
    # Drop the index
    op.drop_index("ix_loads_booked", "loads")

    # Drop all the added columns
    op.drop_column("loads", "miles")
    op.drop_column("loads", "dimensions")
    op.drop_column("loads", "num_of_pieces")
    op.drop_column("loads", "session_id")
    op.drop_column("loads", "booked")
