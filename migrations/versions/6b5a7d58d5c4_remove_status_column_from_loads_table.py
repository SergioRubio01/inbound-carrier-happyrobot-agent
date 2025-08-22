"""Remove status column from loads table

Revision ID: 6b5a7d58d5c4
Revises: remove_rate_add_sentiment
Create Date: 2025-08-22 14:21:36.622930

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "6b5a7d58d5c4"
down_revision: Union[str, None] = "remove_rate_add_sentiment"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Remove the status column from loads table as we now use only the booked boolean field
    op.drop_column("loads", "status")


def downgrade() -> None:
    # Add the status column back in case of rollback
    op.add_column(
        "loads",
        sa.Column(
            "status", sa.String(length=30), nullable=False, server_default="AVAILABLE"
        ),
    )
    # Add index back
    op.create_index("ix_loads_status", "loads", ["status"])
