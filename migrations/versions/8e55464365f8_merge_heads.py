"""merge_heads

Revision ID: 8e55464365f8
Revises: 005_remove_negotiations_table, add_call_metrics_perf_idx
Create Date: 2025-08-21 21:08:14.765623

"""

from typing import Sequence, Union

# revision identifiers, used by Alembic.
revision: str = "8e55464365f8"
down_revision: Union[str, Sequence[str], None] = (
    "005_remove_negotiations_table",
    "add_call_metrics_perf_idx",
)
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
