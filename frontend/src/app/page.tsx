"use client";

import { FormEvent, useEffect, useState } from "react";

import {
  BLANK_PREFERENCES,
  CandidatePreferencesForm,
} from "@/components/job-hunter/candidate-preferences-form";
import { WorkspaceNavigation } from "@/components/job-hunter/workspace-navigation";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  AIMatch,
  ApplicationStatus,
  authenticate,
  CandidatePreferences,
  getAIMatches,
  getApplications,
  getHousingAssistance,
  getJobs,
  getPreferences,
  getResume,
  HousingAssistance,
  importJobs,
  JobApplication,
  Job,
  JobSource,
  ResumeProfile,
  saveApplication,
  savePreferences,
  uploadResume,
} from "@/lib/api";
import { CTA_COPY, WorkspaceSection } from "@/lib/ui-copy";

const fieldClass =
  "min-h-11 w-full rounded-md border border-slate-300 bg-white px-3 text-base outline-none focus:border-blue-700";

function errorMessage(error: unknown) {
  return error instanceof Error ? error.message : "Something went wrong";
}

function jobSalary(job: Job) {
  if (job.salary_min === null && job.salary_max === null) return "Salary not published";
  const values = [job.salary_min, job.salary_max].filter((value) => value !== null);
  return `${job.salary_currency ?? ""} ${values.map((value) => value?.toLocaleString()).join("–")}`;
}

function publicationDate(job: Job) {
  if (!job.published_at) return "Publication date not provided";
  return new Intl.DateTimeFormat("en-GB", { dateStyle: "medium" }).format(
    new Date(job.published_at),
  );
}

export default function Home() {
  const [token, setToken] = useState<string | null>(null);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [register, setRegister] = useState(false);
  const [resume, setResume] = useState<ResumeProfile | null>(null);
  const [preferences, setPreferences] = useState<CandidatePreferences | null>(null);
  const [matches, setMatches] = useState<AIMatch[]>([]);
  const [applications, setApplications] = useState<JobApplication[]>([]);
  const [recentJobs, setRecentJobs] = useState<Job[]>([]);
  const [applicationStatuses, setApplicationStatuses] = useState<Record<number, ApplicationStatus>>({});
  const [housing, setHousing] = useState<Record<number, HousingAssistance>>({});
  const [source, setSource] = useState<JobSource>("arbeitnow");
  const [searchScope, setSearchScope] = useState<"netherlands" | "worldwide_remote">(
    "netherlands",
  );
  const [query, setQuery] = useState("Python");
  const [city, setCity] = useState("");
  const [minimumSalary, setMinimumSalary] = useState("");
  const [workplaceMode, setWorkplaceMode] = useState("");
  const [includeUnknownSalary, setIncludeUnknownSalary] = useState(true);
  const [limit, setLimit] = useState(30);
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(false);
  const [activeSection, setActiveSection] = useState<WorkspaceSection>("today");

  useEffect(() => {
    const frame = requestAnimationFrame(() => {
      const storedToken = sessionStorage.getItem("job-hunter-token");
      setToken(storedToken);
      if (storedToken) void loadWorkspace(storedToken);
    });
    return () => cancelAnimationFrame(frame);
  }, []);

  async function loadWorkspace(accessToken: string) {
    const [resumeResult, preferencesResult, applicationsResult, jobsResult] =
      await Promise.allSettled([
      getResume(accessToken),
      getPreferences(accessToken),
      getApplications(accessToken),
      getJobs(accessToken),
    ]);
    if (resumeResult.status === "fulfilled") {
      setResume(resumeResult.value);
    }
    if (preferencesResult.status === "fulfilled") {
      setPreferences(preferencesResult.value);
      setCity(preferencesResult.value.preferred_cities[0] ?? "");
      setMinimumSalary(
        preferencesResult.value.minimum_salary_gross_annual?.toString() ?? "",
      );
      setWorkplaceMode(
        preferencesResult.value.workplace_modes.length === 1
          ? preferencesResult.value.workplace_modes[0]
          : "",
      );
    } else setActiveSection("profile");
    if (applicationsResult.status === "fulfilled") {
      setApplications(applicationsResult.value);
      setApplicationStatuses(
        Object.fromEntries(applicationsResult.value.map((item) => [item.job_id, item.status])),
      );
    }
    if (jobsResult.status === "fulfilled") setRecentJobs(jobsResult.value);
  }

  async function submitAuth(event: FormEvent) {
    event.preventDefault();
    setLoading(true);
    setMessage("");
    try {
      const result = await authenticate(email, password, register);
      sessionStorage.setItem("job-hunter-token", result.access_token);
      setToken(result.access_token);
      await loadWorkspace(result.access_token);
    } catch (error) {
      setMessage(errorMessage(error));
    } finally {
      setLoading(false);
    }
  }

  async function submitResume(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!token) return;
    const input = event.currentTarget.elements.namedItem("resume") as HTMLInputElement;
    const file = input.files?.[0];
    if (!file) return;
    setLoading(true);
    setMessage("Analysing your CV. The file itself is not stored.");
    try {
      setResume(await uploadResume(token, file));
      setMessage("CV analysed successfully. Review the extracted profile below.");
    } catch (error) {
      setMessage(errorMessage(error));
    } finally {
      setLoading(false);
    }
  }

  async function completeOnboarding(nextPreferences: CandidatePreferences) {
    if (!token) return;
    setLoading(true);
    setMessage("");
    try {
      const saved = await savePreferences(token, nextPreferences);
      setPreferences(saved);
      setCity(saved.preferred_cities[0] ?? "");
      setMinimumSalary(saved.minimum_salary_gross_annual?.toString() ?? "");
      setWorkplaceMode(saved.workplace_modes.length === 1 ? saved.workplace_modes[0] : "");
      setActiveSection("today");
      setMessage("Your preferences were saved. You can update them in Profile at any time.");
    } catch (error) {
      throw new Error(errorMessage(error));
    } finally {
      setLoading(false);
    }
  }

  async function runSearch() {
    if (!token) return;
    if (!resume) {
      setMessage("Analyse your CV before searching for personalised matches.");
      setActiveSection("profile");
      return;
    }
    setLoading(true);
    setMessage("");
    try {
      const imported = await importJobs(token, {
        source,
        query,
        country: "NL",
        scope: searchScope,
        limit: 30,
      });
      setRecentJobs((current) => {
        const importedIds = new Set(imported.jobs.map((job) => job.id));
        return [...imported.jobs, ...current.filter((job) => !importedIds.has(job.id))].slice(0, 30);
      });
      const result = await getAIMatches(token, {
        scope: searchScope,
        country: "NL",
        city: city || undefined,
        minimum_salary: minimumSalary ? Number(minimumSalary) : undefined,
        include_unknown_salary: includeUnknownSalary,
        workplace_mode: workplaceMode
          ? (workplaceMode as "onsite" | "hybrid" | "remote")
          : undefined,
        limit,
      });
      setMatches(result);
      setMessage(
        result.length
          ? `${result.length} jobs analysed (${imported.imported} newly imported). AI scores support—not replace—your review.`
          : `No eligible jobs matched these filters (${imported.imported} newly imported).`,
      );
    } catch (error) {
      setMessage(errorMessage(error));
    } finally {
      setLoading(false);
    }
  }

  async function updateApplication(jobId: number, status: ApplicationStatus) {
    if (!token) return;
    try {
      const updated = await saveApplication(token, jobId, status);
      setApplicationStatuses((current) => ({ ...current, [jobId]: status }));
      setApplications((current) => [
        updated,
        ...current.filter((application) => application.job_id !== jobId),
      ]);
      if (status !== "saved") setMatches((current) => current.filter((item) => item.job_id !== jobId));
    } catch (error) {
      setMessage(errorMessage(error));
    }
  }

  async function showHousing(match: AIMatch) {
    if (!token) return;
    const jobCity = match.job.location.split(",")[0].trim();
    try {
      const result = await getHousingAssistance(token, {
        job_city: jobCity,
        annual_gross_salary: match.job.salary_max ?? match.job.salary_min ?? undefined,
      });
      setHousing((current) => ({ ...current, [match.job_id]: result }));
    } catch (error) {
      setMessage(`${errorMessage(error)} Try a supported main city such as Amsterdam or Utrecht.`);
    }
  }

  function renderMatchCards() {
    if (matches.length === 0) {
      return (
        <Card className="border-dashed py-12 text-center">
          <CardContent>
            <p className="font-semibold">No recommendations yet.</p>
            <p className="mt-2 text-sm text-slate-600">
              Analyse your CV, then search for today&apos;s best matches.
            </p>
            <Button className="mt-5 min-h-11" onClick={() => setActiveSection("search")}>
              Go to search
            </Button>
          </CardContent>
        </Card>
      );
    }

    return matches.map((match) => (
      <Card className="mb-5" key={match.job_id}>
        <CardContent className="pt-6">
          <div className="flex flex-col gap-5 sm:flex-row">
            <div className="grid h-16 w-16 shrink-0 place-items-center rounded-2xl bg-slate-950 text-xl font-black text-cyan-400">
              {match.overall_score}%
            </div>
            <div className="min-w-0 flex-1">
              <div className="flex flex-wrap gap-2">
                <Badge variant="outline">{match.job.source} · {match.job.country}</Badge>
                <Badge>{match.recommendation}</Badge>
                <Badge variant="secondary">
                  {match.legitimacy_status === "source_verified"
                    ? "Source checked"
                    : "Review legitimacy"}
                </Badge>
              </div>
              <h3 className="mt-3 text-xl font-bold">{match.job.title}</h3>
              <p className="text-slate-600">{match.job.company} · {match.job.location}</p>
              <p className="mt-1 text-sm font-medium">
                {jobSalary(match.job)} · {match.job.workplace_mode ?? "Mode unknown"}
              </p>
              <p className="mt-1 text-sm text-slate-600">
                {match.job.employment_type || "Contract not provided"} ·{" "}
                {publicationDate(match.job)}
              </p>
              <div className="mt-4 grid gap-3 text-sm md:grid-cols-2">
                <div className="rounded-lg bg-emerald-50 p-3 text-emerald-950">
                  <strong>Strengths</strong>
                  <ul className="mt-1 list-disc pl-4">
                    {match.strengths.map((item) => <li key={item}>{item}</li>)}
                  </ul>
                </div>
                <div className="rounded-lg bg-amber-50 p-3 text-amber-950">
                  <strong>Gaps to check</strong>
                  <ul className="mt-1 list-disc pl-4">
                    {match.gaps.map((item) => <li key={item}>{item}</li>)}
                  </ul>
                </div>
              </div>
              {match.evidence.length > 0 && (
                <details className="mt-3 text-sm">
                  <summary className="cursor-pointer font-semibold">Verbatim evidence</summary>
                  {match.evidence.map((item, index) => (
                    <p className="mt-2 border-l-2 border-cyan-700 pl-3" key={`${item.cv}-${index}`}>
                      CV: “{item.cv}”<br />Job: “{item.job}”
                    </p>
                  ))}
                </details>
              )}
              {match.legitimacy_reasons.length > 0 && (
                <p className="mt-3 text-xs text-slate-600">
                  Risk-screen notes: {match.legitimacy_reasons.join(", ")}. Verify the vacancy on
                  the employer&apos;s website.
                </p>
              )}
              {match.job.source_attribution && (
                <p className="mt-2 text-xs text-slate-600">{match.job.source_attribution}</p>
              )}
            </div>
            <div className="flex shrink-0 flex-col gap-2">
              <Button className="min-h-11" render={
                <a href={match.job.url} target="_blank" rel="noreferrer" />
              }>
                View original job
              </Button>
              <select
                className={`${fieldClass} min-h-11`}
                aria-label={`Application status for ${match.job.title}`}
                value={applicationStatuses[match.job_id] ?? ""}
                onChange={(event) => {
                  void updateApplication(match.job_id, event.target.value as ApplicationStatus);
                }}
              >
                <option value="" disabled>Track status</option>
                <option value="saved">{CTA_COPY.save}</option>
                <option value="applied">Applied</option>
                <option value="interview">Interview</option>
                <option value="rejected">Rejected</option>
                <option value="offer">Offer</option>
                <option value="withdrawn">Withdrawn</option>
              </select>
              <Button
                className="min-h-11"
                variant="outline"
                onClick={() => { void showHousing(match); }}
              >
                {CTA_COPY.housing}
              </Button>
            </div>
          </div>

          {housing[match.job_id] && (
            <div className="mt-5 rounded-xl border border-slate-200 bg-slate-50 p-4 text-sm">
              <h4 className="font-bold">Housing around {housing[match.job_id].job_city}</h4>
              {housing[match.job_id].affordability && (
                <p className="mt-1">
                  Estimated range: €
                  {housing[match.job_id].affordability!.minimum_monthly_rent.toLocaleString()}–€
                  {housing[match.job_id].affordability!.maximum_monthly_rent.toLocaleString()}/month
                </p>
              )}
              <div className="mt-3 flex flex-wrap gap-3">
                {housing[match.job_id].nearby_cities.map((item) => (
                  <div className="rounded-lg bg-white p-3" key={item.city}>
                    <strong>{item.city}</strong>{" "}
                    <span className="text-slate-600">({item.relation})</span>
                    <div className="mt-2 flex flex-wrap gap-3">
                      {item.provider_links.map((link) => (
                        <a
                          className="min-h-11 content-center text-blue-700 underline"
                          href={link.url}
                          target="_blank"
                          rel="noreferrer"
                          key={link.provider}
                        >
                          {link.provider}
                        </a>
                      ))}
                    </div>
                    <p className="mt-1 text-xs text-amber-800">Registration: verify manually</p>
                  </div>
                ))}
              </div>
              <p className="mt-3 text-xs text-slate-600">
                {housing[match.job_id].data_notice} {housing[match.job_id].guarantee_notice}
              </p>
            </div>
          )}
        </CardContent>
      </Card>
    ));
  }

  if (!token) {
    return (
      <main className="grid min-h-screen bg-slate-950 px-5 py-10 text-slate-100 lg:grid-cols-2 lg:items-center lg:px-20">
        <section className="mx-auto max-w-xl py-12">
          <Badge className="mb-6 bg-cyan-400 text-slate-950">EUROPEAN CAREER COPILOT</Badge>
          <h1 className="text-5xl font-black leading-tight tracking-tight md:text-7xl">
            Find work in the Netherlands with evidence, not guesswork.
          </h1>
          <p className="mt-6 max-w-lg text-lg text-slate-300">
            Analyse your CV, collect permitted job listings and compare up to 30 roles at a time.
          </p>
        </section>
        <Card className="mx-auto w-full max-w-md border-slate-700 bg-slate-900 text-slate-100">
          <CardHeader>
            <CardTitle>{register ? "Create your account" : "Sign in to your workspace"}</CardTitle>
            <CardDescription className="text-slate-400">
              Your CV analysis and applications are isolated to your account.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form className="space-y-5" onSubmit={submitAuth}>
              <Label htmlFor="email">Email</Label>
              <Input id="email" type="email" required value={email}
                className="border-slate-700 bg-slate-950 text-slate-100"
                onChange={(event) => setEmail(event.target.value)} />
              <Label htmlFor="password">Password</Label>
              <Input id="password" type="password" required minLength={register ? 10 : undefined}
                className="border-slate-700 bg-slate-950 text-slate-100"
                value={password} onChange={(event) => setPassword(event.target.value)} />
              {message && <p className="text-sm text-amber-300">{message}</p>}
              <Button type="submit" disabled={loading} className="min-h-11 w-full bg-cyan-400 text-slate-950">
                {loading ? "Working…" : register ? "Create account" : "Sign in"}
              </Button>
              <button type="button" className="min-h-11 w-full rounded-lg px-3 py-2 text-sm font-medium hover:bg-slate-800"
                onClick={() => setRegister((current) => !current)}>
                {register ? "I already have an account" : "Create an account"}
              </button>
            </form>
          </CardContent>
        </Card>
      </main>
    );
  }

  return (
    <main className="min-h-screen bg-slate-50 pb-20 text-slate-950 md:pb-0">
      <header className="border-b border-slate-800 bg-slate-950 px-4 py-4 text-white">
        <div className="mx-auto flex max-w-7xl items-center justify-between gap-4">
          <div>
            <p className="text-xs font-bold tracking-[.22em] text-cyan-400">AI JOB HUNTER</p>
            <p className="text-sm text-slate-300">Private Netherlands job search</p>
          </div>
          <Button
            className="min-h-11 border-slate-600 bg-transparent"
            variant="outline"
            onClick={() => {
              sessionStorage.removeItem("job-hunter-token");
              setToken(null);
            }}
          >
            Sign out
          </Button>
        </div>
      </header>

      <div className="mx-auto flex max-w-7xl gap-6 px-4 py-6 md:px-6 md:py-8">
        <WorkspaceNavigation active={activeSection} onChange={setActiveSection} />

        <div className="min-w-0 flex-1">
          {message && (
            <p role="status" className="mb-5 rounded-xl border border-slate-200 bg-white p-4 text-sm">
              {message}
            </p>
          )}

          {activeSection === "today" && (
            <section aria-labelledby="today-title">
              <p className="text-sm font-semibold text-cyan-800">YOUR DAILY SHORTLIST</p>
              <div className="mb-6 flex flex-wrap items-end justify-between gap-4">
                <div>
                  <h1 id="today-title" className="text-3xl font-bold tracking-tight">
                    Welcome back
                  </h1>
                  <p className="mt-1 text-slate-600">
                    Your strongest current opportunities in one place.
                  </p>
                </div>
                <Button className="min-h-11" onClick={() => setActiveSection("search")}>
                  {CTA_COPY.findJobs}
                </Button>
              </div>
              {preferences ? (
                <Card className="mb-6">
                  <CardContent className="flex flex-col gap-4 pt-6 sm:flex-row sm:items-center">
                    <div className="min-w-0 flex-1">
                      <p className="text-sm font-semibold text-slate-600">Your search profile</p>
                      <p className="mt-1 font-bold">{preferences.target_roles.join(" · ")}</p>
                      <p className="mt-1 text-sm text-slate-600">
                        {preferences.preferred_cities.join(", ")} · English{" "}
                        {preferences.english_level.toUpperCase()} · Dutch{" "}
                        {preferences.dutch_level.toUpperCase()}
                      </p>
                    </div>
                    <Button
                      className="min-h-11"
                      variant="outline"
                      onClick={() => setActiveSection("profile")}
                    >
                      Edit profile
                    </Button>
                  </CardContent>
                </Card>
              ) : (
                <Card className="mb-6 border-dashed">
                  <CardContent className="pt-6">
                    <p className="font-bold">Complete your onboarding first</p>
                    <p className="mt-1 text-sm text-slate-600">
                      Tell us what work you want so Today can be personalised.
                    </p>
                    <Button className="mt-4 min-h-11" onClick={() => setActiveSection("profile")}>
                      Complete profile
                    </Button>
                  </CardContent>
                </Card>
              )}
              <div className="mb-6 grid gap-3 sm:grid-cols-3">
                <Card><CardContent className="pt-5"><strong>{matches.length}</strong><p className="text-sm text-slate-600">Current matches</p></CardContent></Card>
                <Card><CardContent className="pt-5"><strong>{applications.length}</strong><p className="text-sm text-slate-600">Tracked applications</p></CardContent></Card>
                <Card><CardContent className="pt-5"><strong>{preferences ? "Ready" : "Missing"}</strong><p className="text-sm text-slate-600">Onboarding</p></CardContent></Card>
              </div>
              <div className="mb-4 flex items-center justify-between">
                <h2 className="text-2xl font-bold">Jobs for you</h2>
                <Badge variant="secondary">{matches.length}</Badge>
              </div>
              {renderMatchCards()}
              <div className="mb-4 mt-10 flex items-center justify-between">
                <div>
                  <h2 className="text-2xl font-bold">Recent jobs</h2>
                  <p className="text-sm text-slate-600">Latest imported Dutch opportunities.</p>
                </div>
                <Button className="min-h-11" variant="outline"
                  onClick={() => setActiveSection("search")}>
                  Search jobs
                </Button>
              </div>
              {recentJobs.length === 0 ? (
                <Card className="border-dashed py-10 text-center">
                  <CardContent>
                    <p className="font-semibold">No recent jobs imported yet.</p>
                    <p className="mt-1 text-sm text-slate-600">
                      Start a search to collect current opportunities.
                    </p>
                  </CardContent>
                </Card>
              ) : (
                <div className="grid gap-4 lg:grid-cols-2">
                  {recentJobs.slice(0, 6).map((job) => (
                    <Card key={job.id}>
                      <CardContent className="pt-6">
                        <div className="flex flex-wrap gap-2">
                          <Badge variant="outline">{job.source}</Badge>
                          <Badge variant="secondary">No compatibility score</Badge>
                        </div>
                        <h3 className="mt-3 text-lg font-bold">{job.title}</h3>
                        <p className="text-sm text-slate-600">{job.company} · {job.location}</p>
                        <dl className="mt-4 grid gap-2 text-sm sm:grid-cols-2">
                          <div><dt className="font-semibold">Work mode</dt><dd>{job.workplace_mode ?? "Not provided"}</dd></div>
                          <div><dt className="font-semibold">Contract</dt><dd>{job.employment_type || "Not provided"}</dd></div>
                          <div><dt className="font-semibold">Salary</dt><dd>{jobSalary(job)}</dd></div>
                          <div><dt className="font-semibold">Published</dt><dd>{publicationDate(job)}</dd></div>
                        </dl>
                        <div className="mt-5 flex flex-wrap gap-2">
                          <Button className="min-h-11" render={
                            <a href={job.url} target="_blank" rel="noreferrer" />
                          }>
                            View original job
                          </Button>
                          <Button className="min-h-11" variant="outline"
                            disabled={applicationStatuses[job.id] === "saved"}
                            onClick={() => { void updateApplication(job.id, "saved"); }}>
                            {applicationStatuses[job.id] === "saved" ? "Saved" : CTA_COPY.save}
                          </Button>
                        </div>
                      </CardContent>
                    </Card>
                  ))}
                </div>
              )}
            </section>
          )}

          {activeSection === "search" && (
            <section aria-labelledby="search-title">
              <p className="text-sm font-semibold text-cyan-800">NETHERLANDS FIRST</p>
              <h1 id="search-title" className="text-3xl font-bold tracking-tight">Search</h1>
              <p className="mt-1 text-slate-600">
                Search across the Netherlands or switch to remote roles explicitly available from
                the Netherlands or EU.
              </p>
              <Card className="my-6">
                <CardContent className="grid gap-4 pt-6 sm:grid-cols-2">
                  <div className="sm:col-span-2">
                    <Label htmlFor="scope">Search area</Label>
                    <select
                      id="scope"
                      className={`${fieldClass} mt-2 min-h-11`}
                      value={searchScope}
                      onChange={(event) => {
                        const nextScope = event.target.value as
                          | "netherlands"
                          | "worldwide_remote";
                        setSearchScope(nextScope);
                        if (nextScope === "worldwide_remote") setSource("remotive");
                      }}
                    >
                      <option value="netherlands">All Netherlands</option>
                      <option value="worldwide_remote">Worldwide remote (NL/EU eligible)</option>
                    </select>
                  </div>
                  <div className="sm:col-span-2">
                    <Label htmlFor="query">Role or skills</Label>
                    <Input id="query" className="mt-2 min-h-11" value={query}
                      onChange={(event) => setQuery(event.target.value)} />
                  </div>
                  <div>
                    <Label htmlFor="city">Dutch city (optional)</Label>
                    <Input id="city" className="mt-2 min-h-11" placeholder="Amsterdam" value={city}
                      onChange={(event) => setCity(event.target.value)} />
                  </div>
                  <div>
                    <Label htmlFor="salary">Minimum annual gross salary (€)</Label>
                    <Input id="salary" className="mt-2 min-h-11" type="number" min="0"
                      placeholder="45000" value={minimumSalary}
                      onChange={(event) => setMinimumSalary(event.target.value)} />
                  </div>
                  <div>
                    <Label htmlFor="workplace">Workplace</Label>
                    <select id="workplace" className={`${fieldClass} mt-2 min-h-11`}
                      value={workplaceMode} onChange={(event) => setWorkplaceMode(event.target.value)}>
                      <option value="">Any</option>
                      <option value="onsite">On-site</option>
                      <option value="hybrid">Hybrid</option>
                      <option value="remote">Remote</option>
                    </select>
                  </div>
                  <label className="flex min-h-11 items-center gap-3 self-end text-sm">
                    <input type="checkbox" checked={includeUnknownSalary}
                      onChange={(event) => setIncludeUnknownSalary(event.target.checked)} />
                    Include jobs without published salary
                  </label>
                  <details className="sm:col-span-2">
                    <summary className="cursor-pointer py-2 font-semibold">Advanced options</summary>
                    <div className="mt-3 grid gap-4 rounded-xl bg-slate-50 p-4 sm:grid-cols-2">
                      <div>
                        <Label htmlFor="source">Job source</Label>
                        <select id="source" className={`${fieldClass} mt-2 min-h-11`} value={source}
                          onChange={(event) => setSource(event.target.value as JobSource)}>
                          <option value="arbeitnow">Arbeitnow</option>
                          <option value="remotive">Remotive</option>
                          <option value="eures">EURES (experimental)</option>
                          <option value="adzuna_nl">Adzuna NL (credentials required)</option>
                        </select>
                      </div>
                      <div>
                        <Label htmlFor="limit">Maximum results</Label>
                        <select id="limit" className={`${fieldClass} mt-2 min-h-11`} value={limit}
                          onChange={(event) => setLimit(Number(event.target.value))}>
                          <option value={10}>10</option>
                          <option value={20}>20</option>
                          <option value={30}>30</option>
                        </select>
                      </div>
                    </div>
                  </details>
                  <div className="sm:col-span-2">
                    <Button className="min-h-11 w-full sm:w-auto" disabled={loading || !resume}
                      onClick={() => { void runSearch(); }}>
                      {loading ? "Searching…" : CTA_COPY.findJobs}
                    </Button>
                    {!resume && <p className="mt-2 text-sm text-amber-800">Analyse your CV in Profile first.</p>}
                  </div>
                </CardContent>
              </Card>
              <div className="mb-4 flex items-center justify-between">
                <h2 className="text-2xl font-bold">Results</h2>
                <Badge variant="secondary">{matches.length} jobs</Badge>
              </div>
              {renderMatchCards()}
            </section>
          )}

          {activeSection === "applications" && (
            <section aria-labelledby="applications-title">
              <p className="text-sm font-semibold text-cyan-800">YOUR PIPELINE</p>
              <h1 id="applications-title" className="text-3xl font-bold tracking-tight">
                Applications
              </h1>
              <p className="mt-1 text-slate-600">Keep every next step visible.</p>
              <div className="mt-6 space-y-4">
                {applications.length === 0 ? (
                  <Card className="border-dashed py-12 text-center">
                    <CardContent>
                      <p className="font-semibold">No tracked applications yet.</p>
                      <Button className="mt-5 min-h-11" onClick={() => setActiveSection("search")}>
                        Find jobs
                      </Button>
                    </CardContent>
                  </Card>
                ) : applications.map((application) => (
                  <Card key={application.id}>
                    <CardContent className="flex flex-col gap-4 pt-6 sm:flex-row sm:items-center">
                      <div className="min-w-0 flex-1">
                        <Badge>{application.status}</Badge>
                        <h2 className="mt-2 text-lg font-bold">{application.job.title}</h2>
                        <p className="text-sm text-slate-600">
                          {application.job.company} · {application.job.location}
                        </p>
                      </div>
                      <Button className="min-h-11" variant="outline" render={
                        <a href={application.job.url} target="_blank" rel="noreferrer" />
                      }>
                        View original job
                      </Button>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </section>
          )}

          {activeSection === "profile" && (
            <section aria-labelledby="profile-title">
              <p className="text-sm font-semibold text-cyan-800">3-STEP SETUP</p>
              <h1 id="profile-title" className="text-3xl font-bold tracking-tight">Profile</h1>
              <p className="mt-1 text-slate-600">
                Your answers stay private and can be updated at any time.
              </p>
              <Card className="mt-6">
                <CardHeader>
                  <CardTitle>CV analysis</CardTitle>
                  <CardDescription>
                    Optional for onboarding, required for evidence-based AI matching. PDF up to 5 MB.
                  </CardDescription>
                </CardHeader>
                <CardContent className="grid gap-5 lg:grid-cols-2">
                  <form className="space-y-3" onSubmit={submitResume}>
                    <Label htmlFor="resume-upload">CV in PDF</Label>
                    <Input id="resume-upload" className="min-h-11" name="resume" type="file"
                      accept="application/pdf,.pdf" required />
                    <Button type="submit" disabled={loading} className="min-h-11">
                      {CTA_COPY.analyseCv}
                    </Button>
                  </form>
                  <div className="space-y-2 rounded-xl bg-slate-50 p-4 text-sm">
                    {resume ? (
                      <>
                        <p className="font-semibold">{resume.summary ?? "Profile extracted"}</p>
                        <p><strong>Roles:</strong> {resume.target_roles.join(", ") || "Not found"}</p>
                        <p><strong>Skills:</strong> {resume.skills.join(", ") || "Not found"}</p>
                        <p><strong>Languages:</strong> {resume.languages.join(", ") || "Not found"}</p>
                      </>
                    ) : <p className="text-slate-600">No CV has been analysed yet.</p>}
                  </div>
                </CardContent>
              </Card>

              <Card className="mt-6">
                <CardContent className="pt-6">
                  <CandidatePreferencesForm
                    key={preferences?.updated_at ?? resume?.updated_at ?? "new"}
                    initialValue={preferences ?? {
                      ...BLANK_PREFERENCES,
                      target_roles: resume?.target_roles ?? [],
                      skills: resume?.skills ?? [],
                    }}
                    loading={loading}
                    onComplete={completeOnboarding}
                  />
                </CardContent>
              </Card>
            </section>
          )}
        </div>
      </div>
    </main>
  );
}
