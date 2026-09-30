from datetime import UTC, datetime
from html.parser import HTMLParser
from typing import Protocol
from urllib.parse import quote
from uuid import uuid4

import httpx
from pydantic import BaseModel, ConfigDict, Field, HttpUrl, field_validator, model_validator

from app.config import Settings
from app.schemas import JobSource

MAX_DESCRIPTION_CHARACTERS = 20_000
NETHERLANDS_LOCATION_MARKERS = {
    "almere",
    "amersfoort",
    "amsterdam",
    "arnhem",
    "breda",
    "delft",
    "den bosch",
    "den haag",
    "deventer",
    "eindhoven",
    "enschede",
    "groningen",
    "haarlem",
    "hilversum",
    "hoofddorp",
    "leeuwarden",
    "leiden",
    "maastricht",
    "middelburg",
    "netherlands",
    "nederland",
    "nijmegen",
    "rotterdam",
    "schiedam",
    "the hague",
    "tilburg",
    "utrecht",
    "venlo",
    "zwolle",
}
WORLDWIDE_MARKERS = {"anywhere", "global", "worldwide", "world-wide"}
EU_MARKERS = {
    "europe",
    "european union",
    "eu only",
    "emea",
}


class ConnectorDisabledError(Exception):
    pass


class ConnectorResponseError(Exception):
    pass


class _PlainTextParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []
        self.ignored_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in {"script", "style"}:
            self.ignored_depth += 1
        elif tag in {"p", "br", "li", "div"}:
            self.parts.append(" ")

    def handle_endtag(self, tag: str) -> None:
        if tag in {"script", "style"} and self.ignored_depth:
            self.ignored_depth -= 1
        elif tag in {"p", "li", "div"}:
            self.parts.append(" ")

    def handle_data(self, data: str) -> None:
        if not self.ignored_depth:
            self.parts.append(data)


def html_to_text(value: str) -> str:
    parser = _PlainTextParser()
    parser.feed(value[: MAX_DESCRIPTION_CHARACTERS * 3])
    return " ".join("".join(parser.parts).split())[:MAX_DESCRIPTION_CHARACTERS]


def normalized_location(value: str) -> str:
    return " ".join(value.lower().replace(",", " ").replace("/", " ").split())


def is_netherlands_location(value: str) -> bool:
    location = normalized_location(value)
    return any(marker in location for marker in NETHERLANDS_LOCATION_MARKERS)


def remote_scope_for_location(value: str) -> str:
    location = normalized_location(value)
    if is_netherlands_location(location):
        return "netherlands"
    if any(marker in location for marker in WORLDWIDE_MARKERS):
        return "worldwide"
    if any(marker in location for marker in EU_MARKERS):
        return "eu"
    return "unknown"


def location_matches_scope(value: str, scope: str, *, remote: bool) -> bool:
    remote_scope = remote_scope_for_location(value)
    if scope == "netherlands":
        return is_netherlands_location(value)
    return remote and remote_scope in {"netherlands", "eu", "worldwide"}


def country_for_location(value: str) -> str:
    scope = remote_scope_for_location(value)
    if scope == "netherlands":
        return "NL"
    if scope == "eu":
        return "EU"
    if scope == "worldwide":
        return "Worldwide"
    return "Unknown"


def parse_datetime(value: object) -> datetime | None:
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        parsed = datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=UTC)


class NormalizedJob(BaseModel):
    model_config = ConfigDict(extra="forbid")

    external_id: str = Field(min_length=1, max_length=160)
    title: str = Field(min_length=1, max_length=180)
    company: str = Field(default="", max_length=180)
    country: str = Field(min_length=1, max_length=100)
    location: str = Field(default="", max_length=180)
    description: str = Field(min_length=1, max_length=MAX_DESCRIPTION_CHARACTERS)
    url: HttpUrl
    employment_type: str = Field(default="", max_length=80)
    salary_min: float | None = Field(default=None, ge=0, le=10_000_000)
    salary_max: float | None = Field(default=None, ge=0, le=10_000_000)
    salary_currency: str | None = Field(default=None, pattern="^[A-Za-z]{3}$")
    workplace_mode: str | None = Field(default=None, pattern="^(onsite|hybrid|remote)$")
    remote_scope: str | None = Field(
        default=None, pattern="^(netherlands|eu|worldwide|unknown)$"
    )
    published_at: datetime | None = None

    @field_validator("url")
    @classmethod
    def https_only(cls, value: HttpUrl) -> HttpUrl:
        if value.scheme != "https":
            raise ValueError("Connector job URL must use HTTPS")
        return value

    @field_validator("salary_currency")
    @classmethod
    def uppercase_currency(cls, value: str | None) -> str | None:
        return value.upper() if value else None

    @model_validator(mode="after")
    def valid_salary_range(self) -> "NormalizedJob":
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


class JobConnector(Protocol):
    source: JobSource
    attribution: str | None

    async def fetch(
        self, *, query: str, country: str, scope: str, page: int, limit: int
    ) -> list[NormalizedJob]: ...


class BaseConnector:
    source: JobSource
    attribution: str | None = None

    def __init__(self, client: httpx.AsyncClient | None = None) -> None:
        self.client = client

    async def _get(self, url: str, *, params: dict[str, object]) -> object:
        return await self._request("GET", url, params=params)

    async def _post(self, url: str, *, json: dict[str, object]) -> object:
        return await self._request("POST", url, json=json)

    async def _request(self, method: str, url: str, **kwargs: object) -> object:
        owns_client = self.client is None
        client = self.client or httpx.AsyncClient(timeout=15.0)
        try:
            response = await client.request(method, url, **kwargs)
            response.raise_for_status()
            return response.json()
        except (httpx.HTTPError, ValueError) as exc:
            raise ConnectorResponseError(
                "Job source is unavailable or returned invalid data"
            ) from exc
        finally:
            if owns_client:
                await client.aclose()


class ArbeitnowConnector(BaseConnector):
    source = JobSource.ARBEITNOW

    async def fetch(
        self, *, query: str, country: str, scope: str, page: int, limit: int
    ) -> list[NormalizedJob]:
        del country
        payload = await self._get(
            "https://www.arbeitnow.com/api/job-board-api", params={"page": page}
        )
        rows = payload.get("data", []) if isinstance(payload, dict) else []
        results: list[NormalizedJob] = []
        for row in rows:
            if not isinstance(row, dict):
                continue
            haystack = f"{row.get('title', '')} {row.get('description', '')}".lower()
            if query and query.lower() not in haystack:
                continue
            location = str(row.get("location", ""))
            remote = row.get("remote") is True
            if not location_matches_scope(location, scope, remote=remote):
                continue
            try:
                results.append(
                    NormalizedJob(
                        external_id=str(row.get("slug") or row.get("url", "")),
                        title=str(row.get("title", "")),
                        company=str(row.get("company_name", "")),
                        country=country_for_location(location),
                        location=location,
                        description=html_to_text(str(row.get("description", ""))),
                        url=str(row.get("url", "")),
                        employment_type=", ".join(row.get("job_types") or []),
                        workplace_mode="remote" if remote else None,
                        remote_scope=remote_scope_for_location(location) if remote else None,
                        published_at=parse_datetime(row.get("created_at")),
                    )
                )
            except (ValueError, TypeError):
                continue
            if len(results) >= limit:
                break
        return results


class RemotiveConnector(BaseConnector):
    source = JobSource.REMOTIVE
    attribution = "Jobs provided by Remotive (https://remotive.com/remote-jobs)."

    async def fetch(
        self, *, query: str, country: str, scope: str, page: int, limit: int
    ) -> list[NormalizedJob]:
        del country, page
        payload = await self._get(
            "https://remotive.com/api/remote-jobs", params={"search": query, "limit": limit}
        )
        rows = payload.get("jobs", []) if isinstance(payload, dict) else []
        results: list[NormalizedJob] = []
        for row in rows[:limit]:
            if not isinstance(row, dict):
                continue
            location = str(row.get("candidate_required_location", "Remote"))
            if not location_matches_scope(location, scope, remote=True):
                continue
            try:
                results.append(
                    NormalizedJob(
                        external_id=str(row.get("id", "")),
                        title=str(row.get("title", "")),
                        company=str(row.get("company_name", "")),
                        country=country_for_location(location),
                        location=location,
                        description=html_to_text(str(row.get("description", ""))),
                        url=str(row.get("url", "")),
                        employment_type=str(row.get("job_type", "")),
                        workplace_mode="remote",
                        remote_scope=remote_scope_for_location(location),
                        published_at=parse_datetime(row.get("publication_date")),
                    )
                )
            except (ValueError, TypeError):
                continue
        return results


class AdzunaNLConnector(BaseConnector):
    source = JobSource.ADZUNA_NL

    def __init__(self, app_id: str, app_key: str, client: httpx.AsyncClient | None = None) -> None:
        super().__init__(client)
        self.app_id = app_id
        self.app_key = app_key

    async def fetch(
        self, *, query: str, country: str, scope: str, page: int, limit: int
    ) -> list[NormalizedJob]:
        if scope == "worldwide_remote":
            return []
        payload = await self._get(
            f"https://api.adzuna.com/v1/api/jobs/nl/search/{page}",
            params={
                "app_id": self.app_id,
                "app_key": self.app_key,
                "results_per_page": limit,
                "what": query,
            },
        )
        rows = payload.get("results", []) if isinstance(payload, dict) else []
        results: list[NormalizedJob] = []
        for row in rows[:limit]:
            if not isinstance(row, dict):
                continue
            try:
                results.append(
                    NormalizedJob(
                        external_id=str(row.get("id", "")),
                        title=str(row.get("title", "")),
                        company=str((row.get("company") or {}).get("display_name", "")),
                        country=country,
                        location=str((row.get("location") or {}).get("display_name", "")),
                        description=html_to_text(str(row.get("description", ""))),
                        url=str(row.get("redirect_url", "")),
                        employment_type=str(row.get("contract_time", "")),
                        salary_min=row.get("salary_min"),
                        salary_max=row.get("salary_max"),
                        salary_currency=(
                            "EUR"
                            if row.get("salary_min") is not None
                            or row.get("salary_max") is not None
                            else None
                        ),
                        remote_scope=None,
                        published_at=parse_datetime(row.get("created")),
                    )
                )
            except (ValueError, TypeError, AttributeError):
                continue
        return results


class EuresConnector(BaseConnector):
    """Unofficial reverse-engineered EURES portal schema; disabled by default."""

    source = JobSource.EURES

    async def fetch(
        self, *, query: str, country: str, scope: str, page: int, limit: int
    ) -> list[NormalizedJob]:
        if scope == "worldwide_remote":
            return []
        request_body = {
            "resultsPerPage": limit,
            "page": page,
            "sortSearch": "MOST_RECENT",
            "keywords": ([{"keyword": query, "specificSearchCode": "EVERYWHERE"}] if query else []),
            "publicationPeriod": "LAST_MONTH",
            "occupationUris": [],
            "skillUris": [],
            "requiredExperienceCodes": [],
            "positionScheduleCodes": [],
            "sectorCodes": [],
            "educationAndQualificationLevelCodes": [],
            "positionOfferingCodes": [],
            "locationCodes": [country.lower()],
            "euresFlagCodes": [],
            "otherBenefitsCodes": [],
            "requiredLanguages": [],
            "minNumberPost": None,
            "sessionId": str(uuid4()),
            "userPreferredLanguage": None,
            "requestLanguage": "en",
        }
        payload = await self._post(
            "https://europa.eu/eures/api/jv-searchengine/public/jv-search/search",
            json=request_body,
        )
        rows = payload.get("jvs", []) if isinstance(payload, dict) else []
        results: list[NormalizedJob] = []
        for row in rows[:limit]:
            if not isinstance(row, dict):
                continue
            try:
                external_id = str(row.get("id", ""))
                location_map = row.get("locationMap") or {}
                regions = [
                    str(region)
                    for values in location_map.values()
                    for region in (values if isinstance(values, list) else [])
                ]
                results.append(
                    NormalizedJob(
                        external_id=external_id,
                        title=str(row.get("title", "")),
                        company=str((row.get("employer") or {}).get("name", "")),
                        country=country,
                        location=", ".join(regions)[:180],
                        description=html_to_text(str(row.get("description", ""))),
                        url=(
                            "https://europa.eu/eures/portal/jv-se/jv-details/"
                            f"{quote(external_id, safe='')}?lang=en"
                        ),
                        employment_type=str(row.get("positionOfferingCode", "")),
                        published_at=parse_datetime(row.get("publicationDate")),
                    )
                )
            except (ValueError, TypeError, AttributeError):
                continue
        return results


def get_connector(source: JobSource, settings: Settings) -> JobConnector:
    if source == JobSource.ARBEITNOW:
        return ArbeitnowConnector()
    if source == JobSource.REMOTIVE:
        return RemotiveConnector()
    if source == JobSource.EURES:
        if not settings.enable_eures_connector:
            raise ConnectorDisabledError("EURES connector is disabled")
        return EuresConnector()
    if not settings.adzuna_app_id or not settings.adzuna_app_key:
        raise ConnectorDisabledError("Adzuna NL connector is not configured")
    return AdzunaNLConnector(settings.adzuna_app_id, settings.adzuna_app_key)
