# AI Job Hunter — Persistent Project Rules

## Product mission

Build a private, dependable assistant for Alfredo and a small invited circle (partner and,
optionally, family) to find the best realistic first tech job in the Netherlands. The product must
combine fresh, legitimate job opportunities, transparent annual gross salary information, and
practical housing research near each workplace.

Optimise for a reliable daily job-search routine, not for high user volume, engagement, or
speculative features.

Current product decisions:

- The primary UI language is English. A Spanish translation may be added without replacing the
  English portfolio version.
- Separate invited accounts hold separate profiles. One profile targets programming plus
  hospitality/logistics fallback roles; the other targets human resources.
- Default search covers all Netherlands. A separate worldwide-remote scope includes only roles
  explicitly open to candidates in the Netherlands, EU or worldwide.
- Initial preferred cities are Amsterdam, Utrecht, Den Haag, Haarlem, Almere, Middelburg,
  Eindhoven and Rotterdam.
- The post-MVP mobile distribution target is an installable PWA, not separate native applications.

## Non-negotiable product rules

1. Netherlands is the primary market. Preserve country, city, remote/hybrid/on-site mode, source,
   source URL, retrieval time, publication time when available, and annual gross salary currency.
2. Never invent missing salary, location, publication date, workplace mode, employer facts,
   commute time, housing availability, registration permission, or LLM evidence. Use an explicit
   `unknown`/`null` state and explain it in the UI.
3. A minimum-salary comparison is valid only for normalized annual gross EUR values. Do not compare
   unlike currencies or hourly/monthly values without an explicit, tested normalization step.
   Gross-to-net calculations are labelled estimates, record the tax year and assumptions, and
   preserve the source salary. Employer-specific pension or benefits remain unknown unless stated.
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

## UX information architecture

Design for a novice who wants to answer three questions quickly: “What should I apply for today?”,
“What will I earn?”, and “Where could I live near this job?”

- The authenticated primary navigation must contain at most four destinations:
  1. **Today** — fresh recommended jobs and source-health/freshness status.
  2. **Search** — city, salary and work-mode filters plus results.
  3. **Applications** — saved, applied, interview, rejected and offer states.
  4. **Profile** — CV analysis, preferences, account and privacy controls.
- Put technical source configuration and optional credentials under Profile/Settings. Do not make a
  novice choose APIs or understand connector names before finding jobs.
- On desktop, use a compact sidebar or top navigation with text labels. On mobile, use a labelled
  bottom navigation for the same destinations. Icons never replace labels.
- Do not duplicate navigation concepts such as “dashboard”, “workspace”, “matches” and “jobs” when
  they lead to the same task. Use the names above consistently in UI, documentation and routes.
- Keep advanced filters collapsed by default. The visible search fields are city, minimum annual
  gross EUR salary, work mode and “include jobs without salary”.

## Shortest novice journey

- First use is a guided three-step flow with visible progress:
  1. Upload and analyse CV.
  2. Review/edit extracted roles, skills, languages and work authorization.
  3. Choose city/salary preferences and select **Find today's jobs**.
- A returning user lands on Today and needs one action at most to refresh recommendations.
- Import permitted sources together behind one user action. Individual-source controls are an
  advanced diagnostic feature, not part of the normal journey.
- Never force the user to re-enter data already extracted from the CV or saved in preferences.
- Search and matching are one continuous action from the user's perspective. Background import,
  deduplication, risk checks and LLM batching must not become separate wizard pages.
- A result card shows, before expansion: score, title, company, city, work mode, annual gross EUR
  salary or “Not published”, freshness, source, legitimacy state and the primary action.
- The job-detail panel contains evidence, strengths, gaps and original listing. Housing comparison
  is secondary and appears after the job has been opened or saved, not before relevance is clear.
- Updating application status is an inline action. After “Applied”, remove the job from new matches
  and give an immediate undo option instead of a confirmation dialog.
- Preserve entered filters and scroll position when opening and closing job details.
- Every async action has loading, success, empty, partial-failure and retry states. Never leave a
  disabled button without explaining what is missing.

## Visual system and UI rules

Use a clean, professional Netherlands-oriented dashboard, not a futuristic “AI” aesthetic.

- Approved light palette:
  - Page background: `#F8FAFC` (slate 50).
  - Surface: `#FFFFFF`.
  - Primary text: `#0F172A` (slate 900).
  - Secondary text: `#475569` (slate 600).
  - Primary action: `#155E75` (cyan 800) with white text.
  - Accent/highlight: `#22D3EE` (cyan 400) with `#0F172A` text.
  - Focus indicator/link: `#1D4ED8` (blue 700).
  - Success: `#166534`; warning: `#92400E`; error: `#B91C1C`, each on a very light
    same-family background and always accompanied by text/icon.
- These pairings must meet WCAG 2.2 AA: at least 4.5:1 for normal text, 3:1 for large text and UI
  boundaries. Recheck contrast whenever opacity, gradients or states change.
- Use Geist Sans (already aligned with Next.js) for headings, body and controls. Create hierarchy
  with weight and size rather than adding decorative typefaces. If an editorial accent is later
  justified, use Source Serif 4 only for large marketing copy; never use more than two families.
- Default body text is at least 16 px with 1.5 line height. Use a restrained scale: 14 px metadata,
  16 px body/control, 20–24 px card headings and 36–48 px hero heading.
- Use an 8 px spacing system, 12–16 px card radius, one subtle border and minimal shadow. Avoid
  nested cards, glassmorphism, excessive gradients, huge empty hero sections and decorative motion.
- The signed-out hero contains one outcome-led heading, one sentence explaining privacy and value,
  one primary CTA and a quiet sign-in option. Show a compact, realistic result-card preview rather
  than generic AI artwork.
- The signed-in interface prioritizes today's jobs above promotional copy. Do not show a large hero
  after authentication.

## UX copy and calls to action

Use short, specific action copy. Avoid “Submit”, “Continue”, “Working…”, unexplained technical
terms, or exaggerated promises such as “guaranteed”, “perfect job” and “verified employer”.

Approved primary CTA copy and placement:

1. **Analyse my CV** — signed-out hero and CV upload card; only primary CTA before onboarding.
2. **Find today's jobs** — final onboarding step and top of Today when data needs refreshing.
3. **Show my best matches** — Search filter bar, immediately after the essential filters.
4. **Save for later** — every result card as a secondary action beside **View original job**.
5. **Compare housing nearby** — job details after city and salary, never as the card's primary CTA.

- Keep one visually dominant CTA per viewport section. Secondary actions use outline/text styles.
- On mobile, the current task's primary CTA may use a sticky bottom action area, provided it does
  not cover content, keyboard input or bottom navigation.
- Pair destructive/state-changing actions with direct feedback and undo when technically safe.
- Error copy says what happened, whether saved data is safe, and the next action. Never expose
  provider internals, secrets or stack traces.
- Empty states explain why they are empty and offer one relevant action; do not use dead-end copy.

## Accessibility and responsive rules

The five mobile design failures that this project must actively prevent are:

1. Desktop-width layouts causing horizontal scrolling or tiny multi-column cards.
2. Tap targets below 44×44 CSS pixels or controls placed too close together.
3. Text below 16 px for primary content, weak contrast, or meaning communicated only by color.
4. Fixed/sticky headers, banners or CTA bars that cover content or the on-screen keyboard.
5. Heavy media, layout shifts and excessive animation that make interaction slow or unstable.

Required mobile and accessibility checklist:

- Support 320 px width without horizontal scrolling; use one-column forms/cards below the desktop
  breakpoint and test long job titles, company names, locations and translated text.
- Use semantic landmarks, heading order, real buttons/links, associated labels and useful alt text.
- All functionality must work with keyboard only. Focus order follows visual order and a visible
  high-contrast focus ring is never removed.
- Tap targets are at least 44×44 px. Inputs use at least 16 px text to avoid mobile browser zoom.
- Errors are connected to their fields, announced to assistive technology and not indicated by
  color alone. Loading changes use appropriate live regions without repeated announcements.
- Dialogs trap and restore focus, close with Escape and have an accessible name. Prefer a
  responsive detail page/drawer over stacking dialogs.
- Respect `prefers-reduced-motion`; use animation only to explain state change and keep it brief.
- Reserve dimensions for asynchronous content to limit layout shift. Lazy-load noncritical
  content and avoid unnecessary client-side JavaScript.
- Target WCAG 2.2 AA and practical Core Web Vitals: LCP ≤2.5 s, INP ≤200 ms and CLS ≤0.1 at the
  75th percentile when real monitoring is available.
- Test at 320, 375, 768 and 1280 px, portrait and landscape, plus 200% browser zoom.
- Before delivery run automated accessibility checks and manually verify keyboard navigation,
  focus, screen-reader names, responsive overflow, touch targets, loading, empty and error states.

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
