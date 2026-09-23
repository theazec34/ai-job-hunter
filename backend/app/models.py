from datetime import datetime, timezone

from sqlalchemy import JSON, DateTime, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    profile: Mapped["Profile | None"] = relationship(
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
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
