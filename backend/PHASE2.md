# Phase 2 backend notes

- `POST /api/resume` accepts one `multipart/form-data` field named `file`. It requires an
  authenticated user, `application/pdf`, a `%PDF-` header, and a maximum size of 5 MiB. The raw
  PDF is never persisted.
- The LLM is an OpenAI-compatible chat-completions service configured only with `LLM_API_KEY`,
  `LLM_BASE_URL`, and `LLM_MODEL`. The deterministic match fallback is only for local demos and
  is disabled by default. Matching pre-ranks and filters jobs before sending 1-30 candidates in
  sequential batches of at most 10.
- `POST /api/jobs/import` uses the official public Arbeitnow and Remotive APIs, the optional
  official Adzuna NL API, and `eures`. The EURES portal search request and response schema are
  prominently identified as unofficial and reverse-engineered; they may change without notice.
  That connector is disabled by default with `ENABLE_EURES_CONNECTOR=false`. Remotive results
  include attribution that clients must display. LinkedIn and Indeed are intentionally
  unsupported and are never scraped.
- Job salary fields are annual gross normalized values when the source reliably supplies them.
  Missing salary and workplace metadata remain `null`; they are never inferred.
- Applications are unique per user and job. Progressed applications are excluded from that
  user's AI matching, while `saved` jobs remain eligible.
- `POST /api/housing/assistance` provides only a small transparent static nearby-city map,
  affordability estimates, and provider search links. Funda, Pararius, and Kamernet have no
  public official APIs used by this service and are not scraped. Responses are not current
  listings; registration status is always `unknown`, requires manual verification, and carries
  no listing or registration guarantee.
- Legitimacy status is deterministic risk screening based on connector provenance and fraud
  signals. It is not a guarantee that a job or employer is legitimate.
- Startup uses `Base.metadata.create_all()` for fresh demo databases. It does not migrate an
  existing schema. Existing phase-1 database volumes must be recreated before running phase 2;
  use Alembic before retaining production data across schema versions.
