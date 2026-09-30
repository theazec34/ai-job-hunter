import re
from collections.abc import Callable
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.concurrency import run_in_threadpool
from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.config import get_settings
from app.connectors import (
    ConnectorDisabledError,
    ConnectorResponseError,
    JobConnector,
    get_connector,
)
from app.database import get_db
from app.housing import NEARBY_CITIES, housing_assistance
from app.legitimacy import assess_legitimacy
from app.llm import (
    LLMProvider,
    LLMResponseError,
    LLMUnavailableError,
    get_llm_provider,
)
from app.models import Application, Job, Profile, ResumeProfile, User
from app.resumes import ResumeFileError, extract_pdf_text, read_pdf_request
from app.schemas import (
    AIMatchRequest,
    AIMatchResponse,
    ApplicationResponse,
    ApplicationStatus,
    ApplicationUpsert,
    HousingAssistanceRequest,
    HousingAssistanceResponse,
    JobImportRequest,
    JobImportResponse,
    JobInput,
    JobResponse,
    JobSource,
    LoginRequest,
    MatchResponse,
    ProfileInput,
    ProfileResponse,
    RegisterRequest,
    ResumeAnalysis,
    ResumeProfileResponse,
    TokenResponse,
)
from app.security import create_access_token, get_current_user, hash_password, verify_password

router = APIRouter(prefix="/api")
DatabaseSession = Annotated[Session, Depends(get_db)]
AuthenticatedUser = Annotated[User, Depends(get_current_user)]
CountryFilter = Annotated[str | None, Query(max_length=100)]
ResultLimit = Annotated[int, Query(ge=1, le=100)]
LLMDependency = Annotated[LLMProvider, Depends(get_llm_provider)]
ConnectorResolver = Callable[[JobSource], JobConnector]


def get_connector_resolver() -> ConnectorResolver:
    settings = get_settings()
    return lambda source: get_connector(source, settings)


ConnectorDependency = Annotated[ConnectorResolver, Depends(get_connector_resolver)]


@router.post("/auth/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, db: DatabaseSession) -> TokenResponse:
    email = payload.email.lower()
    if db.scalar(select(User).where(User.email == email)):
        raise HTTPException(status_code=409, detail="An account with this email already exists")

    user = User(email=email, password_hash=hash_password(payload.password))
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409, detail="An account with this email already exists"
        ) from None
    db.refresh(user)
    return TokenResponse(access_token=create_access_token(user.id))


@router.post("/auth/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: DatabaseSession) -> TokenResponse:
    user = db.scalar(select(User).where(User.email == payload.email.lower()))
    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    return TokenResponse(access_token=create_access_token(user.id))


@router.get("/profile", response_model=ProfileResponse)
def get_profile(current_user: AuthenticatedUser) -> Profile:
    if current_user.profile is None:
        raise HTTPException(status_code=404, detail="Profile not created")
    return current_user.profile


@router.put("/profile", response_model=ProfileResponse)
def upsert_profile(
    payload: ProfileInput,
    current_user: AuthenticatedUser,
    db: DatabaseSession,
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
    _: AuthenticatedUser,
    db: DatabaseSession,
) -> Job:
    values = payload.model_dump(mode="json")
    assessment = assess_legitimacy(
        source=payload.source.lower(),
        company=payload.company,
        url=str(payload.url),
        description=payload.description,
    )
    job = Job(
        **values,
        legitimacy_status=assessment.status,
        legitimacy_reasons=assessment.reasons,
    )
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
    _: AuthenticatedUser,
    db: DatabaseSession,
    country: CountryFilter = None,
    limit: ResultLimit = 50,
) -> list[Job]:
    statement = select(Job).order_by(Job.created_at.desc()).limit(limit)
    if country:
        statement = statement.where(Job.country.ilike(country))
    return list(db.scalars(statement))


def tokenize(value: str) -> set[str]:
    pattern = r"[a-z0-9+#]+(?:\.[a-z0-9+#]+)*"
    return {word for word in re.findall(pattern, value.lower()) if len(word) > 1}


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
    current_user: AuthenticatedUser,
    db: DatabaseSession,
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


def resume_response(profile: ResumeProfile) -> ResumeProfileResponse:
    return ResumeProfileResponse(
        id=profile.id,
        user_id=profile.user_id,
        target_roles=profile.target_roles,
        skills=profile.skills,
        experience_level=profile.experience_level,
        years_experience=profile.years_experience,
        languages=profile.languages,
        preferred_countries=profile.preferred_countries,
        work_authorization=profile.work_authorization,
        summary=profile.summary,
        extracted_character_count=len(profile.extracted_text),
        updated_at=profile.updated_at,
    )


@router.post(
    "/resume",
    response_model=ResumeProfileResponse,
    openapi_extra={
        "requestBody": {
            "required": True,
            "content": {
                "multipart/form-data": {
                    "schema": {
                        "type": "object",
                        "required": ["file"],
                        "properties": {"file": {"type": "string", "format": "binary"}},
                    }
                }
            },
        }
    },
)
async def upload_resume(
    request: Request,
    current_user: AuthenticatedUser,
    db: DatabaseSession,
    llm: LLMDependency,
) -> ResumeProfileResponse:
    try:
        content = await read_pdf_request(request)
        text = await run_in_threadpool(extract_pdf_text, content)
        analysis = await llm.analyse_resume(text)
    except ResumeFileError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from None
    except LLMUnavailableError:
        raise HTTPException(status_code=503, detail="CV analysis service is unavailable") from None
    except LLMResponseError:
        raise HTTPException(
            status_code=502, detail="CV analysis service returned invalid data"
        ) from None

    profile = db.scalar(select(ResumeProfile).where(ResumeProfile.user_id == current_user.id))
    values = analysis.model_dump()
    if profile is None:
        profile = ResumeProfile(user_id=current_user.id, extracted_text=text, **values)
        db.add(profile)
    else:
        profile.extracted_text = text
        for key, value in values.items():
            setattr(profile, key, value)
    db.commit()
    db.refresh(profile)
    return resume_response(profile)


@router.get("/resume", response_model=ResumeProfileResponse)
def get_resume(current_user: AuthenticatedUser, db: DatabaseSession) -> ResumeProfileResponse:
    profile = db.scalar(select(ResumeProfile).where(ResumeProfile.user_id == current_user.id))
    if profile is None:
        raise HTTPException(status_code=404, detail="Analysed CV not found")
    return resume_response(profile)


@router.post("/jobs/import", response_model=JobImportResponse)
async def import_jobs(
    payload: JobImportRequest,
    _: AuthenticatedUser,
    db: DatabaseSession,
    resolve_connector: ConnectorDependency,
) -> JobImportResponse:
    try:
        connector = resolve_connector(payload.source)
        normalized = await connector.fetch(
            query=payload.query,
            country=payload.country,
            scope=payload.scope,
            page=payload.page,
            limit=payload.limit,
        )
    except ConnectorDisabledError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from None
    except ConnectorResponseError:
        raise HTTPException(status_code=502, detail="Job source is unavailable") from None

    external_ids = [item.external_id for item in normalized]
    existing = set(
        db.scalars(
            select(Job.external_id).where(
                Job.source == payload.source.value,
                Job.external_id.in_(external_ids),
            )
        )
    )
    imported: list[Job] = []
    for item in normalized:
        if item.external_id in existing:
            continue
        assessment = assess_legitimacy(
            source=payload.source.value,
            company=item.company,
            url=str(item.url),
            description=item.description,
        )
        job = Job(
            source=payload.source.value,
            **item.model_dump(mode="json"),
            legitimacy_status=assessment.status,
            legitimacy_reasons=assessment.reasons,
        )
        try:
            with db.begin_nested():
                db.add(job)
                db.flush()
        except IntegrityError:
            existing.add(item.external_id)
            continue
        imported.append(job)
        existing.add(item.external_id)
    db.commit()
    for job in imported:
        db.refresh(job)
    return JobImportResponse(
        source=payload.source,
        imported=len(imported),
        duplicates=len(normalized) - len(imported),
        discarded=0,
        jobs=[JobResponse.model_validate(job) for job in imported],
        attribution=connector.attribution,
    )


def resume_as_analysis(profile: ResumeProfile) -> ResumeAnalysis:
    return ResumeAnalysis(
        target_roles=profile.target_roles,
        skills=profile.skills,
        experience_level=profile.experience_level,
        years_experience=profile.years_experience,
        languages=profile.languages,
        preferred_countries=profile.preferred_countries,
        work_authorization=profile.work_authorization,
        summary=profile.summary,
    )


def deterministic_rank(profile: ResumeProfile, job: Job) -> int:
    resume_terms = tokenize(" ".join([*profile.target_roles, *profile.skills, *profile.languages]))
    job_terms = tokenize(f"{job.title} {job.description}")
    overlap = len(resume_terms & job_terms)
    role_bonus = (
        20 if any(role.lower() in job.title.lower() for role in profile.target_roles) else 0
    )
    return min(100, overlap * 8 + role_bonus)


def deterministic_demo_matches(profile: ResumeProfile, jobs: list[Job]) -> list[AIMatchResponse]:
    results: list[AIMatchResponse] = []
    for job in jobs:
        score = deterministic_rank(profile, job)
        results.append(
            AIMatchResponse(
                job_id=job.id,
                overall_score=score,
                recommendation="apply" if score >= 70 else "review" if score >= 35 else "skip",
                strengths=["Deterministic keyword overlap"] if score else [],
                gaps=[] if score else ["No deterministic keyword overlap"],
                evidence=[],
                job=JobResponse.model_validate(job),
                legitimacy_status=job.legitimacy_status,
                legitimacy_reasons=job.legitimacy_reasons,
                method="deterministic_demo",
            )
        )
    return results


@router.post("/matches/ai", response_model=list[AIMatchResponse])
async def ai_matches(
    payload: AIMatchRequest,
    current_user: AuthenticatedUser,
    db: DatabaseSession,
    llm: LLMDependency,
) -> list[AIMatchResponse]:
    profile = db.scalar(select(ResumeProfile).where(ResumeProfile.user_id == current_user.id))
    if profile is None:
        raise HTTPException(status_code=400, detail="Upload and analyse a CV before AI matching")

    excluded_statuses = [
        ApplicationStatus.APPLIED.value,
        ApplicationStatus.INTERVIEW.value,
        ApplicationStatus.REJECTED.value,
        ApplicationStatus.OFFER.value,
        ApplicationStatus.WITHDRAWN.value,
    ]
    excluded_jobs = select(Application.job_id).where(
        Application.user_id == current_user.id,
        Application.status.in_(excluded_statuses),
    )
    statement = select(Job).where(
        Job.legitimacy_status.in_(["source_verified", "needs_review"]),
        Job.id.not_in(excluded_jobs),
    )
    if payload.scope == "netherlands":
        statement = statement.where(Job.country == "NL")
    else:
        statement = statement.where(
            Job.workplace_mode == "remote",
            Job.remote_scope.in_(["netherlands", "eu", "worldwide"]),
        )
    if payload.city:
        escaped_city = (
            payload.city.strip().replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
        )
        statement = statement.where(Job.location.ilike(f"%{escaped_city}%", escape="\\"))
    salary = func.coalesce(Job.salary_max, Job.salary_min)
    if payload.minimum_salary is not None:
        salary_filter = (Job.salary_currency == "EUR") & (salary >= payload.minimum_salary)
        if payload.include_unknown_salary:
            salary_filter = or_(
                salary_filter,
                (Job.salary_min.is_(None) & Job.salary_max.is_(None)),
            )
        statement = statement.where(salary_filter)
    elif not payload.include_unknown_salary:
        statement = statement.where(or_(Job.salary_min.is_not(None), Job.salary_max.is_not(None)))
    if payload.workplace_mode:
        statement = statement.where(Job.workplace_mode == payload.workplace_mode)
    candidates = list(db.scalars(statement.limit(300)))
    candidates.sort(key=lambda job: deterministic_rank(profile, job), reverse=True)
    candidates = candidates[: payload.limit]
    if not candidates:
        return []

    settings = get_settings()
    try:
        matches = []
        for offset in range(0, len(candidates), 10):
            chunk = candidates[offset : offset + 10]
            jobs_data = [
                {
                    "job_id": job.id,
                    "title": job.title[:180],
                    "company": job.company[:180],
                    "country": job.country[:100],
                    "description": job.description[:8_000],
                }
                for job in chunk
            ]
            batch = await llm.match_jobs(resume_as_analysis(profile), jobs_data)
            expected = {job.id for job in chunk}
            returned = [match.job_id for match in batch.matches]
            if set(returned) != expected or len(returned) != len(expected):
                raise LLMResponseError("invalid_job_ids")
            by_id = {job.id: job for job in chunk}
            for match in batch.matches:
                job = by_id[match.job_id]
                for evidence in match.evidence:
                    if (
                        evidence.cv not in profile.extracted_text
                        or evidence.job not in f"{job.title} {job.description}"
                    ):
                        raise LLMResponseError("unsupported_evidence")
                matches.append((match, job))
    except (LLMUnavailableError, LLMResponseError) as exc:
        if settings.enable_deterministic_demo_matching:
            return deterministic_demo_matches(profile, candidates)
        code = 503 if isinstance(exc, LLMUnavailableError) else 502
        if code == 503:
            detail = "AI matching service is unavailable"
        elif str(exc) == "invalid_job_ids":
            detail = "AI matching service returned invalid job IDs"
        elif str(exc) == "unsupported_evidence":
            detail = "AI matching service returned unsupported evidence"
        else:
            detail = "AI matching service returned invalid data"
        raise HTTPException(status_code=code, detail=detail) from None

    results: list[AIMatchResponse] = []
    for match, job in matches:
        results.append(
            AIMatchResponse(
                **match.model_dump(),
                job=JobResponse.model_validate(job),
                legitimacy_status=job.legitimacy_status,
                legitimacy_reasons=job.legitimacy_reasons,
                method="ai",
            )
        )
    return results


@router.get("/applications", response_model=list[ApplicationResponse])
def list_applications(
    current_user: AuthenticatedUser,
    db: DatabaseSession,
) -> list[Application]:
    statement = (
        select(Application)
        .where(Application.user_id == current_user.id)
        .order_by(Application.updated_at.desc())
    )
    return list(db.scalars(statement))


@router.put("/applications/{job_id}", response_model=ApplicationResponse)
def upsert_application(
    job_id: int,
    payload: ApplicationUpsert,
    current_user: AuthenticatedUser,
    db: DatabaseSession,
) -> Application:
    if db.get(Job, job_id) is None:
        raise HTTPException(status_code=404, detail="Job not found")
    application = db.scalar(
        select(Application).where(
            Application.user_id == current_user.id,
            Application.job_id == job_id,
        )
    )
    if application is None:
        application = Application(
            user_id=current_user.id,
            job_id=job_id,
            status=payload.status.value,
            notes=payload.notes,
        )
        db.add(application)
    else:
        application.status = payload.status.value
        application.notes = payload.notes
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Application update conflicted") from None
    db.refresh(application)
    return application


@router.post("/housing/assistance", response_model=HousingAssistanceResponse)
def get_housing_assistance(
    payload: HousingAssistanceRequest,
    _: AuthenticatedUser,
) -> HousingAssistanceResponse:
    normalized_city = " ".join(payload.job_city.lower().split())
    if normalized_city not in NEARBY_CITIES:
        supported = sorted({value[0] for value in NEARBY_CITIES.values()})
        raise HTTPException(
            status_code=422,
            detail=f"Unsupported city. Supported cities: {', '.join(supported)}",
        )
    return housing_assistance(payload)
