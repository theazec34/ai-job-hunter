# AI Job Hunter

Aplicación full stack para centralizar oportunidades europeas y priorizarlas según el perfil
profesional de cada usuario. La fase 1 incluye autenticación, perfiles aislados, catálogo de
ofertas y un primer motor de puntuación explicable.

## Arquitectura

- **Frontend:** Next.js 16, React 19, TypeScript, Tailwind CSS y componentes shadcn/ui.
- **API:** FastAPI, Pydantic, SQLAlchemy y JWT firmado con HS256.
- **Datos:** PostgreSQL 17.
- **Calidad:** pytest para la API, Ruff para Python y ESLint/TypeScript para el frontend.
- **Ejecución:** Docker Compose con servicios y comprobaciones de salud.

El motor asigna hasta 60 puntos por skills, 25 por coincidencia con el rol deseado y 15 por
país preferido. Es determinista y explica cada coincidencia; no se presenta como una decisión de
IA opaca.

## Inicio rápido con Docker

Requisitos: Docker con Docker Compose.

```bash
cp .env.example .env
# Sustituye POSTGRES_PASSWORD y JWT_SECRET por valores aleatorios y seguros.
docker compose up --build
```

- Aplicación: <http://localhost:43123>
- API y documentación OpenAPI: <http://localhost:8100/docs>
- Salud de la API: <http://localhost:8100/health>

PostgreSQL no se publica fuera de la red interna de Compose. Los datos persisten en el volumen
`postgres_data`.

## Desarrollo local

### Backend

Configura una instancia PostgreSQL y luego:

```bash
cd backend
cp .env.example .env
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
uvicorn app.main:app --reload --port 8100
```

Actualiza `DATABASE_URL`, `JWT_SECRET` y `CORS_ORIGINS` en `backend/.env`. La clave JWT debe tener
32 caracteres como mínimo.

### Frontend

```bash
cd frontend
cp .env.example .env.local
npm ci
npm run dev -- --port 43123
```

Para este modo, establece `NEXT_PUBLIC_API_URL=http://localhost:8100`.

## Pruebas y linting

```bash
cd backend
pytest
ruff check .

cd ../frontend
npm run lint
npm run build
```

Las pruebas usan una base SQLite temporal para ejecutarse sin servicios externos; producción y
Docker usan PostgreSQL.

## API principal

| Método | Ruta | Descripción |
| --- | --- | --- |
| `POST` | `/api/auth/register` | Crea una cuenta y devuelve un JWT |
| `POST` | `/api/auth/login` | Valida credenciales y devuelve un JWT |
| `GET/PUT` | `/api/profile` | Consulta o actualiza el perfil autenticado |
| `GET/POST` | `/api/jobs` | Lista o incorpora ofertas normalizadas |
| `GET` | `/api/matches` | Devuelve ofertas puntuadas para el perfil |

Todas las rutas excepto registro, acceso y salud requieren `Authorization: Bearer <token>`.
Las ofertas se incorporan por API en esta fase. Los conectores EURES u otras fuentes autorizadas
quedan para una fase posterior; no se realiza scraping de LinkedIn ni Indeed.

## Variables de entorno

Nunca subas `.env` al repositorio. Los archivos `.env.example` documentan:

- `DATABASE_URL`: URL SQLAlchemy de PostgreSQL.
- `JWT_SECRET`: secreto aleatorio de al menos 32 caracteres.
- `ACCESS_TOKEN_EXPIRE_MINUTES`: duración del token, entre 5 y 1440 minutos.
- `CORS_ORIGINS`: orígenes web permitidos, separados por comas.
- `NEXT_PUBLIC_API_URL`: URL pública de la API accesible desde el navegador.
- `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`: credenciales de Compose.

## Límites conocidos de la fase 1

- Las tablas se crean al arrancar; antes de evolucionar el esquema se añadirá Alembic.
- No existen todavía conectores externos, refresh tokens, recuperación de contraseña ni roles de
  administración.
- El JWT se conserva en `sessionStorage`, por lo que la sesión termina al cerrar la pestaña. Una
  futura versión puede utilizar una capa BFF con cookie `HttpOnly` y protección CSRF.
- Crear ofertas requiere autenticación, pero todavía no un rol específico; está pensado para
  carga controlada durante la demo.
