"""Update metrics model - remove rate add sentiment

Revision ID: remove_rate_add_sentiment
Revises: 006_add_new_load_fields
Create Date: 2025-08-22 10:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "remove_rate_add_sentiment"
down_revision: Union[str, None] = "006_add_new_load_fields"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Update call_metrics table schema."""
    connection = op.get_bind()
    inspector = sa.inspect(connection)

    # Check if call_metrics table exists
    if "call_metrics" in inspector.get_table_names():
        # Get existing columns
        existing_columns = [
            col["name"] for col in inspector.get_columns("call_metrics")
        ]

        # Create sentiment enum type if it doesn't exist
        try:
            op.execute(
                "CREATE TYPE sentiment_enum AS ENUM ('Positive', 'Neutral', 'Negative')"
            )
        except Exception:
            # Type already exists, which is fine
            pass

        # 1. Remove final_loadboard_rate column if it exists
        if "final_loadboard_rate" in existing_columns:
            op.drop_column("call_metrics", "final_loadboard_rate")

        # 2. Rename reason column to response_reason if reason exists
        if "reason" in existing_columns and "response_reason" not in existing_columns:
            op.alter_column("call_metrics", "reason", new_column_name="response_reason")

        # 3. Add sentiment column if it doesn't exist
        if "sentiment" not in existing_columns:
            op.add_column(
                "call_metrics",
                sa.Column(
                    "sentiment",
                    sa.Enum("Positive", "Neutral", "Negative", name="sentiment_enum"),
                    nullable=True,
                ),
            )

        # 4. Add sentiment_reason column if it doesn't exist
        if "sentiment_reason" not in existing_columns:
            op.add_column(
                "call_metrics", sa.Column("sentiment_reason", sa.Text(), nullable=True)
            )

        # 5. Create new indexes
        existing_indexes = [
            idx["name"] for idx in inspector.get_indexes("call_metrics")
        ]

        if "idx_call_metrics_sentiment" not in existing_indexes:
            op.create_index(
                "idx_call_metrics_sentiment",
                "call_metrics",
                ["sentiment"],
                unique=False,
            )


def downgrade() -> None:
    """Revert call_metrics table schema changes."""
    connection = op.get_bind()
    inspector = sa.inspect(connection)

    # Check if call_metrics table exists
    if "call_metrics" in inspector.get_table_names():
        existing_columns = [
            col["name"] for col in inspector.get_columns("call_metrics")
        ]
        existing_indexes = [
            idx["name"] for idx in inspector.get_indexes("call_metrics")
        ]

        # 1. Drop sentiment index if it exists
        if "idx_call_metrics_sentiment" in existing_indexes:
            op.drop_index("idx_call_metrics_sentiment", table_name="call_metrics")

        # 2. Remove sentiment_reason column if it exists
        if "sentiment_reason" in existing_columns:
            op.drop_column("call_metrics", "sentiment_reason")

        # 3. Remove sentiment column if it exists
        if "sentiment" in existing_columns:
            op.drop_column("call_metrics", "sentiment")

        # 4. Rename response_reason back to reason if response_reason exists
        if "response_reason" in existing_columns and "reason" not in existing_columns:
            op.alter_column("call_metrics", "response_reason", new_column_name="reason")

        # 5. Add back final_loadboard_rate column if it doesn't exist
        if "final_loadboard_rate" not in existing_columns:
            op.add_column(
                "call_metrics",
                sa.Column(
                    "final_loadboard_rate",
                    sa.NUMERIC(precision=10, scale=2),
                    nullable=True,
                ),
            )

        # 6. Drop sentiment enum type if no other tables use it
        try:
            op.execute("DROP TYPE sentiment_enum")
        except Exception:
            # Type might be in use by other tables or not exist, which is fine
            pass
