from datetime import date, datetime
from enum import StrEnum
from typing import Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    HttpUrl,
    field_validator,
    model_validator,
)


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=10, max_length=128)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class ProfileInput(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    headline: str = Field(default="", max_length=180)
    skills: list[str] = Field(default_factory=list, max_length=50)
    desired_roles: list[str] = Field(default_factory=list, max_length=20)
    preferred_countries: list[str] = Field(default_factory=list, max_length=30)

    @field_validator("skills", "desired_roles", "preferred_countries")
    @classmethod
    def normalize_items(cls, values: list[str]) -> list[str]:
        cleaned = [value.strip() for value in values if value.strip()]
        if any(len(value) > 100 for value in cleaned):
            raise ValueError("Each item must contain at most 100 characters")
        return list(dict.fromkeys(cleaned))


class ProfileResponse(ProfileInput):
    id: int
    user_id: int
    model_config = ConfigDict(from_attributes=True)


class CandidatePreferencesInput(BaseModel):
    target_roles: list[str] = Field(min_length=1, max_length=12)
    experience_level: Literal["no_experience", "junior", "mid", "senior", "lead"]
    skills: list[str] = Field(default_factory=list, max_length=50)
    job_types: list[
        Literal["technology", "human_resources", "hospitality", "logistics", "other"]
    ] = Field(min_length=1, max_length=5)
    preferred_cities: list[str] = Field(min_length=1, max_length=20)
    workplace_modes: list[Literal["onsite", "hybrid", "remote"]] = Field(
        min_length=1, max_length=3
    )
    schedules: list[Literal["full_time", "part_time", "temporary", "internship", "freelance"]] = (
        Field(min_length=1, max_length=5)
    )
    minimum_salary_gross_annual: float | None = Field(default=None, ge=0, le=1_000_000)
    available_from: date | None = None
    lives_in_netherlands: bool
    needs_relocation: bool
    dutch_level: Literal["none", "a1", "a2", "b1", "b2", "c1", "c2", "native"]
    english_level: Literal["none", "a1", "a2", "b1", "b2", "c1", "c2", "native"]
    work_authorization: Literal["eu_citizen", "permit", "requires_visa", "unknown"]
    sponsorship_required: bool = False
    onboarding_complete: bool = True

    @field_validator("target_roles", "skills", "preferred_cities")
    @classmethod
    def normalize_preference_items(cls, values: list[str]) -> list[str]:
        cleaned = [value.strip() for value in values if value.strip()]
        if any(len(value) > 120 for value in cleaned):
            raise ValueError("Each preference item must contain at most 120 characters")
        return list(dict.fromkeys(cleaned))


class CandidatePreferencesResponse(CandidatePreferencesInput):
    id: int
    user_id: int
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


class JobInput(BaseModel):
    source: str = Field(min_length=1, max_length=50)
    external_id: str = Field(min_length=1, max_length=160)
    title: str = Field(min_length=1, max_length=180)
    company: str = Field(min_length=1, max_length=180)
    country: str = Field(min_length=1, max_length=100)
    location: str = Field(default="", max_length=180)
    description: str = Field(min_length=1, max_length=20_000)
    url: HttpUrl
    employment_type: str = Field(default="", max_length=80)
    salary_min: float | None = Field(default=None, ge=0, le=10_000_000)
    salary_max: float | None = Field(default=None, ge=0, le=10_000_000)
    salary_currency: str | None = Field(default=None, pattern="^[A-Za-z]{3}$")
    workplace_mode: Literal["onsite", "hybrid", "remote"] | None = None
    remote_scope: Literal["netherlands", "eu", "worldwide", "unknown"] | None = None

    @field_validator("url")
    @classmethod
    def require_https(cls, value: HttpUrl) -> HttpUrl:
        if value.scheme != "https":
            raise ValueError("Job URL must use HTTPS")
        return value

    @field_validator("salary_currency")
    @classmethod
    def uppercase_currency(cls, value: str | None) -> str | None:
        return value.upper() if value else None

    @model_validator(mode="after")
    def validate_salary_range(self) -> "JobInput":
        if (
            self.salary_min is not None
            and self.salary_max is not None
            and self.salary_min > self.salary_max
        ):
            raise ValueError("salary_min cannot exceed salary_max")
        has_salary = self.salary_min is not None or self.salary_max is not None
        if has_salary != (self.salary_currency is not None):
            raise ValueError("salary_currency and salary values must be supplied together")
        return self


class JobResponse(JobInput):
    id: int
    legitimacy_status: Literal["source_verified", "needs_review", "rejected"] = "needs_review"
    legitimacy_reasons: list[str] = Field(default_factory=list)
    source_attribution: str | None = None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class MatchResponse(BaseModel):
    job: JobResponse
    score: int = Field(ge=0, le=100)
    reasons: list[str]


class StrictOutput(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


class ResumeAnalysis(StrictOutput):
    target_roles: list[str] = Field(default_factory=list, max_length=20)
    skills: list[str] = Field(default_factory=list, max_length=100)
    experience_level: Literal["entry", "mid", "senior", "lead", "executive"] | None = None
    years_experience: int | None = Field(default=None, ge=0, le=80)
    languages: list[str] = Field(default_factory=list, max_length=30)
    preferred_countries: list[str] = Field(default_factory=list, max_length=30)
    work_authorization: list[str] = Field(default_factory=list, max_length=30)
    summary: str | None = Field(default=None, max_length=1_000)

    @field_validator(
        "target_roles",
        "skills",
        "languages",
        "preferred_countries",
        "work_authorization",
    )
    @classmethod
    def validate_bounded_items(cls, values: list[str]) -> list[str]:
        if any(not value.strip() or len(value) > 120 for value in values):
            raise ValueError("Items must contain 1-120 non-whitespace characters")
        return list(dict.fromkeys(value.strip() for value in values))


class ResumeProfileResponse(ResumeAnalysis):
    id: int
    user_id: int
    extracted_character_count: int
    updated_at: datetime


class JobSource(StrEnum):
    EURES = "eures"
    ARBEITNOW = "arbeitnow"
    REMOTIVE = "remotive"
    ADZUNA_NL = "adzuna_nl"


class JobImportRequest(BaseModel):
    source: JobSource
    query: str = Field(default="", max_length=100)
    country: str = Field(default="NL", min_length=2, max_length=2)
    scope: Literal["netherlands", "worldwide_remote"] = "netherlands"
    page: int = Field(default=1, ge=1, le=20)
    limit: int = Field(default=20, ge=1, le=50)

    @field_validator("country")
    @classmethod
    def uppercase_country(cls, value: str) -> str:
        return value.upper()


class JobImportResponse(BaseModel):
    source: JobSource
    imported: int
    duplicates: int
    discarded: int
    jobs: list[JobResponse]
    attribution: str | None = None
    risk_notice: str = "Risk screening is not a guarantee that a job or employer is legitimate."


class EvidencePair(StrictOutput):
    cv: str = Field(min_length=1, max_length=300)
    job: str = Field(min_length=1, max_length=300)


class LLMJobMatch(StrictOutput):
    job_id: int
    overall_score: int = Field(ge=0, le=100)
    recommendation: Literal["apply", "review", "skip"]
    strengths: list[str] = Field(max_length=10)
    gaps: list[str] = Field(max_length=10)
    evidence: list[EvidencePair] = Field(max_length=10)

    @field_validator("strengths", "gaps")
    @classmethod
    def validate_match_items(cls, values: list[str]) -> list[str]:
        if any(not item.strip() or len(item) > 300 for item in values):
            raise ValueError("Match items must contain 1-300 non-whitespace characters")
        return values


class LLMMatchBatch(StrictOutput):
    matches: list[LLMJobMatch] = Field(max_length=10)


class AIMatchResponse(LLMJobMatch):
    job: JobResponse
    legitimacy_status: Literal["source_verified", "needs_review"]
    legitimacy_reasons: list[str]
    method: Literal["ai", "deterministic_demo"]


class AIMatchRequest(BaseModel):
    scope: Literal["netherlands", "worldwide_remote"] = "netherlands"
    country: str | None = Field(default=None, max_length=100)
    city: str | None = Field(default=None, min_length=1, max_length=100)
    minimum_salary: float | None = Field(default=None, ge=0, le=10_000_000)
    include_unknown_salary: bool = True
    workplace_mode: Literal["onsite", "hybrid", "remote"] | None = None
    limit: int = Field(default=10, ge=1, le=30)


class ApplicationStatus(StrEnum):
    SAVED = "saved"
    APPLIED = "applied"
    INTERVIEW = "interview"
    REJECTED = "rejected"
    OFFER = "offer"
    WITHDRAWN = "withdrawn"


class ApplicationUpsert(BaseModel):
    status: ApplicationStatus
    notes: str | None = Field(default=None, max_length=2_000)

    @field_validator("notes")
    @classmethod
    def normalize_notes(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        return normalized or None


class ApplicationResponse(BaseModel):
    id: int
    user_id: int
    job_id: int
    status: ApplicationStatus
    notes: str | None
    created_at: datetime
    updated_at: datetime
    job: JobResponse
    model_config = ConfigDict(from_attributes=True)


class HousingAssistanceRequest(BaseModel):
    job_city: str = Field(min_length=1, max_length=100)
    annual_gross_salary: float | None = Field(default=None, gt=0, le=1_000_000)
    max_monthly_rent: float | None = Field(default=None, gt=0, le=20_000)


class HousingProviderLink(BaseModel):
    provider: Literal["Funda", "Pararius", "Kamernet"]
    url: HttpUrl
    relationship: Literal["provider_search_link"] = "provider_search_link"


class HousingCitySuggestion(BaseModel):
    city: str
    relation: str
    registration_status: Literal["unknown"] = "unknown"
    provider_links: list[HousingProviderLink]


class AffordabilityEstimate(BaseModel):
    minimum_monthly_rent: float
    maximum_monthly_rent: float
    label: Literal["estimate"] = "estimate"
    basis: str


class HousingAssistanceResponse(BaseModel):
    job_city: str
    nearby_cities: list[HousingCitySuggestion]
    affordability: AffordabilityEstimate | None
    manual_verification_checklist: list[str]
    guarantee_notice: str
    data_notice: str
