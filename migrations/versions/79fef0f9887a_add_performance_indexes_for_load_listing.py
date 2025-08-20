"""add_performance_indexes_for_load_listing

Revision ID: 79fef0f9887a
Revises: 002_add_sample_data
Create Date: 2025-08-20 16:11:36.021874

"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "79fef0f9887a"
down_revision: Union[str, None] = "002_add_sample_data"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add compound indexes for common filtering and sorting patterns
    op.create_index(
        "ix_loads_status_created_at", "loads", ["status", "created_at"], unique=False
    )

    op.create_index(
        "ix_loads_equipment_status", "loads", ["equipment_type", "status"], unique=False
    )

    op.create_index(
        "ix_loads_pickup_date_status", "loads", ["pickup_date", "status"], unique=False
    )

    op.create_index("ix_loads_deleted_at", "loads", ["deleted_at"], unique=False)


def downgrade() -> None:
    # Drop the added indexes
    op.drop_index("ix_loads_deleted_at", "loads")
    op.drop_index("ix_loads_pickup_date_status", "loads")
    op.drop_index("ix_loads_equipment_status", "loads")
    op.drop_index("ix_loads_status_created_at", "loads")
