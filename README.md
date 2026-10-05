# AI Job Hunter

A full-stack career assistant that analyses a PDF CV, collects jobs from permitted sources and
uses an LLM to explain how well up to 30 opportunities fit the candidate. The current product slice
focuses on the Netherlands, application tracking and transparent housing research links.

The signed-in workspace is organised into **Today**, **Search**, **Applications** and **Profile**.
Profile contains a persistent, accessible three-step onboarding flow. Search separates all Dutch
jobs from worldwide remote roles that explicitly accept Netherlands/EU/worldwide candidates.

> AI scores are decision support, not facts. Job legitimacy, salary, rental availability and
> municipal registration must always be verified independently.

## Architecture

- **Frontend:** Next.js 16, React 19, TypeScript, Tailwind CSS and shadcn/ui.
- **API:** FastAPI, Pydantic, SQLAlchemy and HS256-signed JWTs.
- **Data:** PostgreSQL 17 with per-user CV profiles and application tracking.
- **AI:** OpenAI-compatible 4Geeks Gateway, configured for GPT-6 Luna.
- **Sources:** Arbeitnow and Remotive; optional Adzuna NL and experimental EURES connectors.
- **Quality:** pytest, Ruff, ESLint and TypeScript production builds.
- **Runtime:** Docker Compose with service health checks.

## Quick start with Docker

Requirements: Docker with Docker Compose.

```bash
cp .env.example .env
# Replace POSTGRES_PASSWORD, JWT_SECRET and LLM_API_KEY with private values.
# Replace REGISTRATION_ALLOWLIST with the two invited account emails.
docker compose up --build
```

- Application: <http://localhost:43123>
- API and OpenAPI documentation: <http://localhost:8100/docs>
- API health: <http://localhost:8100/health>

PostgreSQL is not exposed outside the Compose network. Data persists in `postgres_data`.

## Local development

### Backend

Configure a PostgreSQL instance, then:

```bash
cd backend
cp .env.example .env
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
alembic upgrade head
uvicorn app.main:app --reload --port 8100
```

Update `DATABASE_URL`, `JWT_SECRET`, `CORS_ORIGINS` and `LLM_API_KEY` in `backend/.env`. The JWT
secret must contain at least 32 characters. Never commit either `.env` file or paste an API token
into an issue, chat, screenshot or source file.

### Frontend

```bash
cd frontend
cp .env.example .env.local
npm ci
npm run dev -- --port 43123
```

For local development, set `NEXT_PUBLIC_API_URL=http://localhost:8100`.

## Tests and static checks

```bash
cd backend
pytest
ruff check .

cd ../frontend
npm run lint
npm run build
```

Tests use a temporary SQLite database so that they can run without external services. Production
and Docker use PostgreSQL.

## Main API

| Method | Route | Description |
| --- | --- | --- |
| `POST` | `/api/auth/register` | Create an account and return a JWT |
| `POST` | `/api/auth/login` | Validate credentials and return a JWT |
| `GET/PUT` | `/api/profile` | Read or update the authenticated profile |
| `GET/PUT` | `/api/preferences` | Read or update onboarding and search preferences |
| `GET/POST` | `/api/jobs` | List or add normalised jobs |
| `GET` | `/api/jobs/{job_id}` | Return one authenticated job detail |
| `POST` | `/api/resume` | Validate a PDF, extract text and analyse the CV |
| `GET` | `/api/resume` | Return the current user's extracted CV profile |
| `POST` | `/api/jobs/import` | Import and deduplicate an authorised source |
| `POST` | `/api/matches/ai` | Filter and analyse at most 30 jobs in batches of 10 |
| `GET` | `/api/applications` | List the current user's tracked applications |
| `PUT` | `/api/applications/{job_id}` | Save or update an application status |
| `POST` | `/api/housing/assistance` | Return nearby-city guidance and provider search links |

Every route except registration, login and health requires `Authorization: Bearer <token>`.
Progressed applications (`applied`, `interview`, `rejected`, `offer` or `withdrawn`) are excluded
from later AI matching. A `saved` job remains eligible.

Production Compose is invite-only. `REGISTRATION_ALLOWLIST` contains the exact comma-separated
emails permitted to create accounts. Two Gmail aliases such as `name+alfredo@gmail.com` and
`name+ester@gmail.com` arrive in the same inbox while remaining distinct application accounts.
Each person chooses their own password; passwords and invitation emails are never committed.

## Job sources and risk screening

- **Arbeitnow:** public job-board API.
- **Remotive:** public API; its required attribution is preserved in API and UI responses.
- **Adzuna NL:** official API, enabled when `ADZUNA_APP_ID` and `ADZUNA_APP_KEY` are configured.
- **EURES:** public portal endpoint with a reverse-engineered schema. It is experimental and
  disabled by default with `ENABLE_EURES_CONNECTOR=false`.
- **LinkedIn and Indeed:** never scraped.

Imports use two checks: source allowlisting and deterministic fraud-signal screening. Results may
be `source_verified`, `needs_review` or `rejected`, but no automated check can prove that an
employer or vacancy is legitimate. Confirm the role on the employer's own domain before applying.

## CV and LLM privacy

Only PDF files up to 5 MB are accepted. The backend extracts text and stores the resulting text and
structured profile for the authenticated user; it does not persist the uploaded PDF. The extracted
text is sent to the configured LLM provider for analysis. Do not upload a CV unless you accept that
provider's privacy and retention terms.

The default OpenAI-compatible configuration is:

```env
LLM_BASE_URL=https://llm.4geeks.ai
LLM_MODEL=madrid-spain/opnerouter/openai/gpt-6-luna
LLM_TIMEOUT_SECONDS=60
```

The backend treats CVs and job descriptions as untrusted prompt data, validates strict JSON
responses and rejects evidence that is not a verbatim excerpt of the supplied CV and job. If the
gateway returns `404` for `/chat/completions`, test `https://llm.4geeks.ai/v1` as the base URL with
your own local key. Never put the key in Git.

## Salary and housing semantics

Minimum salary filters compare annual gross **EUR** values only. Unknown salaries can be included
or excluded explicitly; the application does not invent missing values.

Funda, Pararius and Kamernet do not expose public listing APIs used by this project. Housing
assistance therefore provides static nearby-city suggestions, affordability estimates and search
links to those providers. It does not scrape listings or claim live availability. A
`registration_status` of `unknown` means the user must verify municipal registration permission
in the signed lease.

## Environment variables

Never commit `.env`. The example files document:

- `DATABASE_URL`: PostgreSQL SQLAlchemy URL.
- `JWT_SECRET`: random secret with at least 32 characters.
- `ACCESS_TOKEN_EXPIRE_MINUTES`: token lifetime between 5 and 1,440 minutes.
- `CORS_ORIGINS`: comma-separated browser origins.
- `NEXT_PUBLIC_API_URL`: public API URL used by the browser.
- `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`: Compose database credentials.
- `LLM_API_KEY`, `LLM_BASE_URL`, `LLM_MODEL`, `LLM_TIMEOUT_SECONDS`: private provider credentials
  and OpenAI-compatible gateway settings.
- `ENABLE_EURES_CONNECTOR`: opt in to the experimental EURES portal connector.
- `ADZUNA_APP_ID`, `ADZUNA_APP_KEY`: optional official Adzuna API credentials.
- `REQUIRE_INVITE`, `REGISTRATION_ALLOWLIST`: close public registration and list invited emails.

## Known limitations

- Alembic owns the database schema. Run `alembic upgrade head` after pulling changes and before
  starting the API. The baseline migration adopts an existing phase-one schema without deleting
  users, profiles or jobs.
- Review generated migrations before applying them to retained data and take a database backup
  before production upgrades.
- Refresh tokens, password recovery and administrative roles are not implemented.
- The JWT is stored in `sessionStorage`, so the browser session ends with the tab. A future BFF
  can move it into an `HttpOnly` cookie with CSRF protection.
- Job creation and imports require authentication but not an administrative role; this remains a
  controlled portfolio demonstration rather than a multi-tenant production service.

## What I learned

This project is helping me practise API boundaries, relational data modelling, authentication,
input validation, automated testing and containerised local development. I use coding assistants
as part of the workflow, then validate changes with tests, static analysis and manual checks.
