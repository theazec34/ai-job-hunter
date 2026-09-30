"""baseline phase two schema

Revision ID: d3bc58a00d0d
Revises:
Create Date: 2026-09-30 18:24:23.457480

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision: str = "d3bc58a00d0d"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def table_names() -> set[str]:
    return set(sa.inspect(op.get_bind()).get_table_names())


def column_names(table: str) -> set[str]:
    return {column["name"] for column in sa.inspect(op.get_bind()).get_columns(table)}


def index_names(table: str) -> set[str]:
    return {index["name"] for index in sa.inspect(op.get_bind()).get_indexes(table)}


def upgrade() -> None:
    """Create a fresh schema or adopt an unmanaged phase-one schema."""
    tables = table_names()
    if "users" not in tables:
        op.create_table(
            "users",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("email", sa.String(length=320), nullable=False),
            sa.Column("password_hash", sa.String(length=255), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.UniqueConstraint("email"),
        )
        op.create_index("ix_users_email", "users", ["email"], unique=True)

    tables = table_names()
    if "profiles" not in tables:
        op.create_table(
            "profiles",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("user_id", sa.Integer(), nullable=False),
            sa.Column("name", sa.String(length=120), nullable=False),
            sa.Column("headline", sa.String(length=180), nullable=False),
            sa.Column("skills", sa.JSON(), nullable=False),
            sa.Column("desired_roles", sa.JSON(), nullable=False),
            sa.Column("preferred_countries", sa.JSON(), nullable=False),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
            sa.UniqueConstraint("user_id"),
        )
        op.create_index("ix_profiles_user_id", "profiles", ["user_id"], unique=True)

    tables = table_names()
    if "jobs" not in tables:
        op.create_table(
            "jobs",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("source", sa.String(length=50), nullable=False),
            sa.Column("external_id", sa.String(length=160), nullable=False),
            sa.Column("title", sa.String(length=180), nullable=False),
            sa.Column("company", sa.String(length=180), nullable=False),
            sa.Column("country", sa.String(length=100), nullable=False),
            sa.Column("location", sa.String(length=180), nullable=False),
            sa.Column("description", sa.Text(), nullable=False),
            sa.Column("url", sa.String(length=2048), nullable=False),
            sa.Column("employment_type", sa.String(length=80), nullable=False),
            sa.Column("salary_min", sa.Float(), nullable=True),
            sa.Column("salary_max", sa.Float(), nullable=True),
            sa.Column("salary_currency", sa.String(length=3), nullable=True),
            sa.Column("workplace_mode", sa.String(length=20), nullable=True),
            sa.Column(
                "legitimacy_status",
                sa.String(length=30),
                server_default="needs_review",
                nullable=False,
            ),
            sa.Column(
                "legitimacy_reasons",
                sa.JSON(),
                server_default=sa.text("'[]'"),
                nullable=False,
            ),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.UniqueConstraint("source", "external_id", name="uq_job_source_external"),
        )
        op.create_index("ix_jobs_source", "jobs", ["source"], unique=False)
        op.create_index("ix_jobs_title", "jobs", ["title"], unique=False)
        op.create_index("ix_jobs_country", "jobs", ["country"], unique=False)
        op.create_index(
            "ix_jobs_legitimacy_status", "jobs", ["legitimacy_status"], unique=False
        )
    else:
        columns = column_names("jobs")
        new_columns = [
            sa.Column("salary_min", sa.Float(), nullable=True),
            sa.Column("salary_max", sa.Float(), nullable=True),
            sa.Column("salary_currency", sa.String(length=3), nullable=True),
            sa.Column("workplace_mode", sa.String(length=20), nullable=True),
            sa.Column(
                "legitimacy_status",
                sa.String(length=30),
                server_default="needs_review",
                nullable=False,
            ),
            sa.Column(
                "legitimacy_reasons",
                sa.JSON(),
                server_default=sa.text("'[]'"),
                nullable=False,
            ),
        ]
        for column in new_columns:
            if column.name not in columns:
                op.add_column("jobs", column)
        if "ix_jobs_legitimacy_status" not in index_names("jobs"):
            op.create_index(
                "ix_jobs_legitimacy_status", "jobs", ["legitimacy_status"], unique=False
            )

    if "resume_profiles" not in table_names():
        op.create_table(
            "resume_profiles",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("user_id", sa.Integer(), nullable=False),
            sa.Column("extracted_text", sa.Text(), nullable=False),
            sa.Column("target_roles", sa.JSON(), nullable=False),
            sa.Column("skills", sa.JSON(), nullable=False),
            sa.Column("experience_level", sa.String(length=50), nullable=True),
            sa.Column("years_experience", sa.Integer(), nullable=True),
            sa.Column("languages", sa.JSON(), nullable=False),
            sa.Column("preferred_countries", sa.JSON(), nullable=False),
            sa.Column("work_authorization", sa.JSON(), nullable=False),
            sa.Column("summary", sa.Text(), nullable=True),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
            sa.UniqueConstraint("user_id"),
        )
        op.create_index(
            "ix_resume_profiles_user_id", "resume_profiles", ["user_id"], unique=True
        )

    if "applications" not in table_names():
        op.create_table(
            "applications",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("user_id", sa.Integer(), nullable=False),
            sa.Column("job_id", sa.Integer(), nullable=False),
            sa.Column("status", sa.String(length=20), nullable=False),
            sa.Column("notes", sa.Text(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.ForeignKeyConstraint(["job_id"], ["jobs.id"]),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
            sa.UniqueConstraint("user_id", "job_id", name="uq_application_user_job"),
        )
        op.create_index("ix_applications_user_id", "applications", ["user_id"], unique=False)
        op.create_index("ix_applications_job_id", "applications", ["job_id"], unique=False)
        op.create_index("ix_applications_status", "applications", ["status"], unique=False)


def downgrade() -> None:
    """Remove phase-two additions while preserving the phase-one baseline."""
    tables = table_names()
    if "applications" in tables:
        op.drop_table("applications")
    if "resume_profiles" in tables:
        op.drop_table("resume_profiles")
    if "jobs" in tables:
        indexes = index_names("jobs")
        if "ix_jobs_legitimacy_status" in indexes:
            op.drop_index("ix_jobs_legitimacy_status", table_name="jobs")
        columns = column_names("jobs")
        for name in [
            "legitimacy_reasons",
            "legitimacy_status",
            "workplace_mode",
            "salary_currency",
            "salary_max",
            "salary_min",
        ]:
            if name in columns:
                op.drop_column("jobs", name)
