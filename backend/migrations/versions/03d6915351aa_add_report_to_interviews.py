"""add_report_to_interviews

Revision ID: 03d6915351aa
Revises: b71f946cb9e8
Create Date: 2026-07-05 01:08:55.996111

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "03d6915351aa"
down_revision: Union[str, Sequence[str], None] = "b71f946cb9e8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column("interviews", sa.Column("report", sa.JSON(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("interviews", "report")
