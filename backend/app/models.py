from datetime import UTC, date, datetime

from sqlalchemy import (
    JSON,
    Boolean,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def utc_now() -> datetime:
    return datetime.now(UTC)


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    profile: Mapped["Profile | None"] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    resume_profile: Mapped["ResumeProfile | None"] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    preferences: Mapped["CandidatePreferences | None"] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )


class Profile(Base):
    __tablename__ = "profiles"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(120))
    headline: Mapped[str] = mapped_column(String(180), default="")
    skills: Mapped[list[str]] = mapped_column(JSON, default=list)
    desired_roles: Mapped[list[str]] = mapped_column(JSON, default=list)
    preferred_countries: Mapped[list[str]] = mapped_column(JSON, default=list)
    user: Mapped[User] = relationship(back_populates="profile")


class ResumeProfile(Base):
    __tablename__ = "resume_profiles"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True, index=True)
    extracted_text: Mapped[str] = mapped_column(Text)
    target_roles: Mapped[list[str]] = mapped_column(JSON, default=list)
    skills: Mapped[list[str]] = mapped_column(JSON, default=list)
    experience_level: Mapped[str | None] = mapped_column(String(50), nullable=True)
    years_experience: Mapped[int | None] = mapped_column(Integer, nullable=True)
    languages: Mapped[list[str]] = mapped_column(JSON, default=list)
    preferred_countries: Mapped[list[str]] = mapped_column(JSON, default=list)
    work_authorization: Mapped[list[str]] = mapped_column(JSON, default=list)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now
    )
    user: Mapped[User] = relationship(back_populates="resume_profile")


class CandidatePreferences(Base):
    __tablename__ = "candidate_preferences"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True, index=True)
    target_roles: Mapped[list[str]] = mapped_column(JSON, default=list)
    experience_level: Mapped[str] = mapped_column(String(30))
    skills: Mapped[list[str]] = mapped_column(JSON, default=list)
    job_types: Mapped[list[str]] = mapped_column(JSON, default=list)
    preferred_cities: Mapped[list[str]] = mapped_column(JSON, default=list)
    workplace_modes: Mapped[list[str]] = mapped_column(JSON, default=list)
    schedules: Mapped[list[str]] = mapped_column(JSON, default=list)
    minimum_salary_gross_annual: Mapped[float | None] = mapped_column(Float, nullable=True)
    available_from: Mapped[date | None] = mapped_column(Date, nullable=True)
    lives_in_netherlands: Mapped[bool] = mapped_column(Boolean, default=False)
    needs_relocation: Mapped[bool] = mapped_column(Boolean, default=False)
    dutch_level: Mapped[str] = mapped_column(String(10))
    english_level: Mapped[str] = mapped_column(String(10))
    work_authorization: Mapped[str] = mapped_column(String(30))
    sponsorship_required: Mapped[bool] = mapped_column(Boolean, default=False)
    onboarding_complete: Mapped[bool] = mapped_column(Boolean, default=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now
    )
    user: Mapped[User] = relationship(back_populates="preferences")


class Job(Base):
    __tablename__ = "jobs"
    __table_args__ = (UniqueConstraint("source", "external_id", name="uq_job_source_external"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    source: Mapped[str] = mapped_column(String(50), index=True)
    external_id: Mapped[str] = mapped_column(String(160))
    title: Mapped[str] = mapped_column(String(180), index=True)
    company: Mapped[str] = mapped_column(String(180))
    country: Mapped[str] = mapped_column(String(100), index=True)
    location: Mapped[str] = mapped_column(String(180), default="")
    description: Mapped[str] = mapped_column(Text)
    url: Mapped[str] = mapped_column(String(2048))
    employment_type: Mapped[str] = mapped_column(String(80), default="")
    salary_min: Mapped[float | None] = mapped_column(Float, nullable=True)
    salary_max: Mapped[float | None] = mapped_column(Float, nullable=True)
    salary_currency: Mapped[str | None] = mapped_column(String(3), nullable=True)
    workplace_mode: Mapped[str | None] = mapped_column(String(20), nullable=True)
    remote_scope: Mapped[str | None] = mapped_column(String(20), nullable=True)
    legitimacy_status: Mapped[str] = mapped_column(String(30), default="needs_review", index=True)
    legitimacy_reasons: Mapped[list[str]] = mapped_column(JSON, default=list)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    @property
    def source_attribution(self) -> str | None:
        if self.source.lower() == "remotive":
            return "Jobs provided by Remotive (https://remotive.com/remote-jobs)."
        return None


class Application(Base):
    __tablename__ = "applications"
    __table_args__ = (UniqueConstraint("user_id", "job_id", name="uq_application_user_job"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    job_id: Mapped[int] = mapped_column(ForeignKey("jobs.id"), index=True)
    status: Mapped[str] = mapped_column(String(20), index=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now
    )
    job: Mapped[Job] = relationship()
    user: Mapped[User] = relationship()
