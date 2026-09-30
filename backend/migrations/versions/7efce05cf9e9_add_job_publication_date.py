"""add job publication date

Revision ID: 7efce05cf9e9
Revises: 2fc6536fe723
Create Date: 2026-09-30 18:59:31.106252

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "7efce05cf9e9"
down_revision: str | Sequence[str] | None = "2fc6536fe723"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "jobs",
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("jobs", "published_at")
