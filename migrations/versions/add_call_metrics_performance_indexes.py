"""add_call_metrics_performance_indexes

Revision ID: add_call_metrics_perf_idx
Revises: 034e2428cb92
Create Date: 2025-08-21 QA Review

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "add_call_metrics_perf_idx"
down_revision: Union[str, None] = "034e2428cb92"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Check if table exists before adding indexes
    connection = op.get_bind()
    inspector = sa.inspect(connection)

    if 'call_metrics' in inspector.get_table_names():
        # Get existing indexes
        existing_indexes = [idx['name'] for idx in inspector.get_indexes('call_metrics')]

        # Add indexes for commonly queried fields in call_metrics table
        if "idx_call_metrics_response" not in existing_indexes:
            op.create_index(
                "idx_call_metrics_response", "call_metrics", ["response"], unique=False
            )

        if "idx_call_metrics_created_at" not in existing_indexes:
            op.create_index(
                "idx_call_metrics_created_at", "call_metrics", ["created_at"], unique=False
            )

        if "idx_call_metrics_response_created_at" not in existing_indexes:
            op.create_index(
                "idx_call_metrics_response_created_at",
                "call_metrics",
                ["response", "created_at"],
                unique=False,
            )


def downgrade() -> None:
    # Remove the performance indexes
    op.drop_index("idx_call_metrics_response_created_at", table_name="call_metrics")
    op.drop_index("idx_call_metrics_created_at", table_name="call_metrics")
    op.drop_index("idx_call_metrics_response", table_name="call_metrics")
