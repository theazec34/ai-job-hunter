"""add remote job scope

Revision ID: b7e8cc315170
Revises: d3bc58a00d0d
Create Date: 2026-09-30 18:51:50.407333

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "b7e8cc315170"
down_revision: str | Sequence[str] | None = "d3bc58a00d0d"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column("jobs", sa.Column("remote_scope", sa.String(length=20), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("jobs", "remote_scope")
