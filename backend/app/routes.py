import re

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Job, Profile, User
from app.schemas import (
    JobInput,
    JobResponse,
    LoginRequest,
    MatchResponse,
    ProfileInput,
    ProfileResponse,
    RegisterRequest,
    TokenResponse,
)
from app.security import create_access_token, get_current_user, hash_password, verify_password

router = APIRouter(prefix="/api")


@router.post("/auth/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, db: Session = Depends(get_db)) -> TokenResponse:
    email = payload.email.lower()
    if db.scalar(select(User).where(User.email == email)):
        raise HTTPException(status_code=409, detail="An account with this email already exists")

    user = User(email=email, password_hash=hash_password(payload.password))
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="An account with this email already exists") from None
    db.refresh(user)
    return TokenResponse(access_token=create_access_token(user.id))


@router.post("/auth/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    user = db.scalar(select(User).where(User.email == payload.email.lower()))
    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    return TokenResponse(access_token=create_access_token(user.id))


@router.get("/profile", response_model=ProfileResponse)
def get_profile(current_user: User = Depends(get_current_user)) -> Profile:
    if current_user.profile is None:
        raise HTTPException(status_code=404, detail="Profile not created")
    return current_user.profile


@router.put("/profile", response_model=ProfileResponse)
def upsert_profile(
    payload: ProfileInput,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Profile:
    profile = current_user.profile
    if profile is None:
        profile = Profile(user_id=current_user.id, **payload.model_dump())
        db.add(profile)
    else:
        for key, value in payload.model_dump().items():
            setattr(profile, key, value)
    db.commit()
    db.refresh(profile)
    return profile


@router.post("/jobs", response_model=JobResponse, status_code=status.HTTP_201_CREATED)
def create_job(
    payload: JobInput,
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Job:
    job = Job(**payload.model_dump(mode="json"))
    db.add(job)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="This source job already exists") from None
    db.refresh(job)
    return job


@router.get("/jobs", response_model=list[JobResponse])
def list_jobs(
    country: str | None = Query(default=None, max_length=100),
    limit: int = Query(default=50, ge=1, le=100),
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[Job]:
    statement = select(Job).order_by(Job.created_at.desc()).limit(limit)
    if country:
        statement = statement.where(Job.country.ilike(country))
    return list(db.scalars(statement))


def tokenize(value: str) -> set[str]:
    return {word for word in re.findall(r"[a-z0-9+#.]+", value.lower()) if len(word) > 1}


def score_job(profile: Profile, job: Job) -> tuple[int, list[str]]:
    job_words = tokenize(f"{job.title} {job.description}")
    skills = {skill.lower() for skill in profile.skills}
    matched_skills = sorted(skill for skill in skills if tokenize(skill) <= job_words)
    role_match = any(role.lower() in job.title.lower() for role in profile.desired_roles)
    country_match = any(
        country.lower() == job.country.lower() for country in profile.preferred_countries
    )

    score = min(60, len(matched_skills) * 15)
    reasons = [f"Skill: {skill}" for skill in matched_skills]
    if role_match:
        score += 25
        reasons.append("Desired role matches the title")
    if country_match:
        score += 15
        reasons.append("Preferred country")
    return min(score, 100), reasons or ["No profile criteria matched"]


@router.get("/matches", response_model=list[MatchResponse])
def list_matches(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[MatchResponse]:
    if current_user.profile is None:
        raise HTTPException(status_code=400, detail="Create your profile before matching jobs")
    jobs = list(db.scalars(select(Job).order_by(Job.created_at.desc()).limit(100)))
    matches = [
        MatchResponse(job=JobResponse.model_validate(job), score=score, reasons=reasons)
        for job in jobs
        for score, reasons in [score_job(current_user.profile, job)]
    ]
    return sorted(matches, key=lambda match: match.score, reverse=True)
