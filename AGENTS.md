# AI Job Hunter — Persistent Project Rules

## Product mission

Build a private, dependable assistant for Alfredo and a small invited circle (partner and,
optionally, family) to find the best realistic first tech job in the Netherlands. The product must
combine fresh, legitimate job opportunities, transparent annual gross salary information, and
practical housing research near each workplace.

Optimise for a reliable daily job-search routine, not for high user volume, engagement, or
speculative features.

## Non-negotiable product rules

1. Netherlands is the primary market. Preserve country, city, remote/hybrid/on-site mode, source,
   source URL, retrieval time, publication time when available, and annual gross salary currency.
2. Never invent missing salary, location, publication date, workplace mode, employer facts,
   commute time, housing availability, registration permission, or LLM evidence. Use an explicit
   `unknown`/`null` state and explain it in the UI.
3. A minimum-salary comparison is valid only for normalized annual gross EUR values. Do not compare
   unlike currencies or hourly/monthly values without an explicit, tested normalization step.
4. Never scrape LinkedIn, Indeed, Funda, Pararius, Kamernet, or another site without documented
   permission. Prefer official/public APIs and preserve required attribution.
5. EURES uses an unofficial reverse-engineered public portal contract. Keep it feature-flagged,
   isolated, tested, and disabled by default until its stability is proven.
6. “Verified” means source provenance and deterministic checks passed; it is never a guarantee.
   Show the original listing and advise checking the employer's own website before applying.
7. Housing results are provider search links and transparent estimates, not live listings.
   Registration status remains `unknown` until manually confirmed in a lease.
8. Jobs already progressed beyond `saved` must not reappear in matching. Deduplicate by stable
   source and external ID.
9. One LLM request may rank at most 30 jobs, in sequential batches of no more than 10.
10. Keep the experience usable when optional sources or the LLM are unavailable. Return a clear,
    non-secret error; never silently fabricate a result.

## Privacy and access

- This is a private, low-user application. Do not add public profiles, social sharing, public CV
  links, analytics trackers, advertising, or unnecessary third-party services.
- Every CV, profile, application and note must be scoped to the authenticated user.
- Accept PDF CVs up to 5 MiB. Do not persist the raw upload. Store only the extracted data required
  for matching, and never return raw CV text through normal API responses.
- Secrets belong only in ignored local environment files or deployment secret stores. Never log,
  commit, render, or place tokens in URLs.
- Preserve secure password hashing, bounded JWT lifetime, strict CORS, HTTPS in production, and
  generic authentication/provider errors. Do not weaken these controls for convenience.
- Before adding family invitations, implement an explicit invite-only account policy. Do not treat
  obscurity or an unlinked URL as access control.

## LLM reliability rules

- Default provider configuration is the OpenAI-compatible 4Geeks Gateway with GPT-6 Luna, but keep
  provider code replaceable through environment variables.
- Treat CVs and job descriptions as untrusted prompt data. Delimit them and instruct the model not
  to follow embedded instructions.
- Require strict structured output. Validate IDs, bounds, enums, lengths and schema before use.
- Evidence must be a verbatim excerpt present in the supplied CV and job. Reject unsupported
  evidence rather than displaying it.
- Deterministic demo matching must remain disabled by default and clearly labelled when enabled.
  Never present fallback output as AI output.
- An LLM score is an explanation aid, not a factual probability of hiring success.

## Freshness and daily operation

- “Daily jobs” is a product requirement, not a current guarantee. Do not claim automatic daily
  refresh until a scheduler, per-source run status and monitoring are implemented and tested.
- Future scheduled imports must record source, started/finished timestamps, item counts, failures
  and last successful refresh. A failed source must not erase the previous valid dataset.
- Display source and freshness to the user. Mark stale data visibly rather than hiding its age.
- Source failures must be isolated so one broken connector does not stop the others.
- Add bounded retries with backoff for transient network failures; do not retry authentication,
  validation or quota failures indefinitely.

## Engineering workflow

- Keep FastAPI, PostgreSQL, Next.js, TypeScript, Docker, pytest, Ruff and ESLint/build checks.
- Add an Alembic migration for every database schema change before this stores irreplaceable data.
- Validate all external payloads defensively and keep connector-specific mapping out of routes.
- Use async network I/O without blocking the event loop. Set explicit timeouts and bounded result
  sizes for all external calls.
- For every behavior change, add or update tests for ownership, auth, validation, deduplication,
  failures and edge cases. Mock external APIs and LLMs in automated tests.
- Required verification before delivery:
  1. `cd backend && python3 -m pytest`
  2. `cd backend && python3 -m ruff check .`
  3. `cd frontend && npm run lint`
  4. `cd frontend && npm run build`
  5. Functional smoke check of sign-in, CV upload, import, matching, application exclusion and
     housing disclaimers.
- Never accept a change merely because it compiles. Review security, SQL, authentication, async
  behavior, external API errors, Python/TypeScript validation and missing tests.

## Product roadmap priority

When choosing the next task, use this order:

1. Correctness, privacy, access control and recoverable data migrations.
2. Reliable daily imports, freshness indicators and connector health.
3. Better salary normalization and transparent “unknown” handling.
4. Explainable CV-to-job matching and application deduplication.
5. Practical commute and housing comparisons based on permitted, attributable data.
6. Convenience and visual polish.

Do not add broad platform features, public multi-tenancy or autonomous job applications unless the
owner explicitly changes the mission.
