"""add candidate preferences

Revision ID: 2fc6536fe723
Revises: b7e8cc315170
Create Date: 2026-09-30 18:54:30.619926

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision: str = "2fc6536fe723"
down_revision: str | Sequence[str] | None = "b7e8cc315170"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "candidate_preferences",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("target_roles", sa.JSON(), nullable=False),
        sa.Column("experience_level", sa.String(length=30), nullable=False),
        sa.Column("skills", sa.JSON(), nullable=False),
        sa.Column("job_types", sa.JSON(), nullable=False),
        sa.Column("preferred_cities", sa.JSON(), nullable=False),
        sa.Column("workplace_modes", sa.JSON(), nullable=False),
        sa.Column("schedules", sa.JSON(), nullable=False),
        sa.Column("minimum_salary_gross_annual", sa.Float(), nullable=True),
        sa.Column("available_from", sa.Date(), nullable=True),
        sa.Column("lives_in_netherlands", sa.Boolean(), nullable=False),
        sa.Column("needs_relocation", sa.Boolean(), nullable=False),
        sa.Column("dutch_level", sa.String(length=10), nullable=False),
        sa.Column("english_level", sa.String(length=10), nullable=False),
        sa.Column("work_authorization", sa.String(length=30), nullable=False),
        sa.Column("sponsorship_required", sa.Boolean(), nullable=False),
        sa.Column("onboarding_complete", sa.Boolean(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.UniqueConstraint("user_id"),
    )
    op.create_index(
        "ix_candidate_preferences_user_id",
        "candidate_preferences",
        ["user_id"],
        unique=True,
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("candidate_preferences")
