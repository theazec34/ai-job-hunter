from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, HttpUrl, field_validator


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


class JobResponse(JobInput):
    id: int
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class MatchResponse(BaseModel):
    job: JobResponse
    score: int = Field(ge=0, le=100)
    reasons: list[str]
