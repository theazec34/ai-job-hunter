# AI Job Hunter

A full-stack application for collecting European job opportunities and ranking them against each
user's professional profile. Phase one includes account authentication, isolated user profiles, a
normalised job catalogue and an explainable matching engine.

> This is an active learning project. The current matcher is deterministic, not an opaque AI
> system: up to 60 points for skills, 25 for a target-role match and 15 for a preferred country.

## Architecture

- **Frontend:** Next.js 16, React 19, TypeScript, Tailwind CSS and shadcn/ui.
- **API:** FastAPI, Pydantic, SQLAlchemy and HS256-signed JWTs.
- **Data:** PostgreSQL 17.
- **Quality:** pytest, Ruff, ESLint and TypeScript production builds.
- **Runtime:** Docker Compose with service health checks.

## Quick start with Docker

Requirements: Docker with Docker Compose.

```bash
cp .env.example .env
# Replace POSTGRES_PASSWORD and JWT_SECRET with strong random values.
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
uvicorn app.main:app --reload --port 8100
```

Update `DATABASE_URL`, `JWT_SECRET` and `CORS_ORIGINS` in `backend/.env`. The JWT secret must
contain at least 32 characters.

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
| `GET/POST` | `/api/jobs` | List or add normalised jobs |
| `GET` | `/api/matches` | Return scored jobs for the current profile |

Every route except registration, login and health requires `Authorization: Bearer <token>`. Jobs
are added through the API during phase one. Future connectors will use authorised sources such as
EURES; the application does not scrape LinkedIn or Indeed.

## Environment variables

Never commit `.env`. The example files document:

- `DATABASE_URL`: PostgreSQL SQLAlchemy URL.
- `JWT_SECRET`: random secret with at least 32 characters.
- `ACCESS_TOKEN_EXPIRE_MINUTES`: token lifetime between 5 and 1,440 minutes.
- `CORS_ORIGINS`: comma-separated browser origins.
- `NEXT_PUBLIC_API_URL`: public API URL used by the browser.
- `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`: Compose database credentials.

## Known phase-one limitations

- Tables are created on startup; schema migrations are the next backend milestone.
- External connectors, refresh tokens, password recovery and administrative roles are not
  implemented yet.
- The JWT is stored in `sessionStorage`, so the browser session ends with the tab. A future BFF
  can move it into an `HttpOnly` cookie with CSRF protection.
- Job creation requires authentication but not an administrative role; it is intended for a
  controlled demonstration environment.

## What I learned

This project is helping me practise API boundaries, relational data modelling, authentication,
input validation, automated testing and containerised local development. I use coding assistants
as part of the workflow, then validate changes with tests, static analysis and manual checks.
