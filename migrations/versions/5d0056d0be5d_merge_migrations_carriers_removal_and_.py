"""Merge migrations: carriers removal and status field removal

Revision ID: 5d0056d0be5d
Revises: 6b5a7d58d5c4, a975eddf0d3d
Create Date: 2025-08-22 18:14:49.556109

"""

from typing import Sequence, Union

# revision identifiers, used by Alembic.
revision: str = "5d0056d0be5d"
down_revision: Union[str, Sequence[str], None] = ("6b5a7d58d5c4", "a975eddf0d3d")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
