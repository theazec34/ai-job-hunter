"use client";

import { FormEvent, useEffect, useState } from "react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  AIMatch,
  ApplicationStatus,
  authenticate,
  getAIMatches,
  getApplications,
  getHousingAssistance,
  getResume,
  HousingAssistance,
  importJobs,
  JobSource,
  ResumeProfile,
  saveApplication,
  uploadResume,
} from "@/lib/api";

const fieldClass =
  "h-9 w-full rounded-md border border-slate-300 bg-white px-3 text-sm outline-none focus:border-cyan-600";

function errorMessage(error: unknown) {
  return error instanceof Error ? error.message : "Something went wrong";
}

function salary(match: AIMatch) {
  const { job } = match;
  if (job.salary_min === null && job.salary_max === null) return "Salary not published";
  const values = [job.salary_min, job.salary_max].filter((value) => value !== null);
  return `${job.salary_currency ?? ""} ${values.map((value) => value?.toLocaleString()).join("–")}`;
}

export default function Home() {
  const [token, setToken] = useState<string | null>(null);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [register, setRegister] = useState(false);
  const [resume, setResume] = useState<ResumeProfile | null>(null);
  const [matches, setMatches] = useState<AIMatch[]>([]);
  const [applicationStatuses, setApplicationStatuses] = useState<Record<number, ApplicationStatus>>({});
  const [housing, setHousing] = useState<Record<number, HousingAssistance>>({});
  const [source, setSource] = useState<JobSource>("arbeitnow");
  const [query, setQuery] = useState("Python");
  const [city, setCity] = useState("");
  const [minimumSalary, setMinimumSalary] = useState("");
  const [workplaceMode, setWorkplaceMode] = useState("");
  const [includeUnknownSalary, setIncludeUnknownSalary] = useState(true);
  const [limit, setLimit] = useState(30);
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const frame = requestAnimationFrame(() => {
      const storedToken = sessionStorage.getItem("job-hunter-token");
      setToken(storedToken);
      if (storedToken) void loadWorkspace(storedToken);
    });
    return () => cancelAnimationFrame(frame);
  }, []);

  async function loadWorkspace(accessToken: string) {
    const [resumeResult, applicationsResult] = await Promise.allSettled([
      getResume(accessToken),
      getApplications(accessToken),
    ]);
    if (resumeResult.status === "fulfilled") setResume(resumeResult.value);
    if (applicationsResult.status === "fulfilled") {
      setApplicationStatuses(
        Object.fromEntries(applicationsResult.value.map((item) => [item.job_id, item.status])),
      );
    }
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

  async function runImport() {
    if (!token) return;
    setLoading(true);
    setMessage("");
    try {
      const result = await importJobs(token, { source, query, country: "NL", limit: 30 });
      setMessage(
        `${result.imported} jobs imported, ${result.duplicates} already known. ${result.attribution ?? ""}`,
      );
    } catch (error) {
      setMessage(errorMessage(error));
    } finally {
      setLoading(false);
    }
  }

  async function runMatching() {
    if (!token) return;
    setLoading(true);
    setMessage("");
    try {
      const result = await getAIMatches(token, {
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
          ? `${result.length} jobs analysed. AI scores support—not replace—your review.`
          : "No eligible jobs matched these filters.",
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
      await saveApplication(token, jobId, status);
      setApplicationStatuses((current) => ({ ...current, [jobId]: status }));
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
              <Button disabled={loading} className="w-full bg-cyan-400 text-slate-950">
                {loading ? "Working…" : register ? "Create account" : "Sign in"}
              </Button>
              <button type="button" className="w-full rounded-lg px-3 py-2 text-sm font-medium hover:bg-slate-800"
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
    <main className="min-h-screen bg-slate-100 text-slate-950">
      <header className="border-b bg-slate-950 px-5 py-5 text-white">
        <div className="mx-auto flex max-w-7xl items-center justify-between">
          <div>
            <p className="text-xs font-bold tracking-[.25em] text-cyan-400">AI JOB HUNTER</p>
            <h1 className="text-xl font-semibold">Netherlands opportunity workspace</h1>
          </div>
          <Button variant="outline" onClick={() => {
            sessionStorage.removeItem("job-hunter-token");
            setToken(null);
          }}>Sign out</Button>
        </div>
      </header>

      <div className="mx-auto grid max-w-7xl gap-6 px-5 py-8 lg:grid-cols-[360px_1fr]">
        <aside className="space-y-5">
          <Card>
            <CardHeader>
              <CardTitle>1. Analyse your CV</CardTitle>
              <CardDescription>PDF only, maximum 5 MB. Extracted text is stored; the PDF is not.</CardDescription>
            </CardHeader>
            <CardContent>
              <form className="space-y-3" onSubmit={submitResume}>
                <Input name="resume" type="file" accept="application/pdf,.pdf" required />
                <Button disabled={loading} className="w-full">Upload and analyse</Button>
              </form>
              {resume && (
                <div className="mt-4 space-y-2 rounded-lg bg-slate-100 p-3 text-sm">
                  <p className="font-semibold">{resume.summary ?? "Profile extracted"}</p>
                  <p><strong>Roles:</strong> {resume.target_roles.join(", ") || "Not found"}</p>
                  <p><strong>Skills:</strong> {resume.skills.join(", ") || "Not found"}</p>
                  <p><strong>Languages:</strong> {resume.languages.join(", ") || "Not found"}</p>
                </div>
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>2. Import jobs</CardTitle>
              <CardDescription>Uses permitted APIs. LinkedIn and Indeed are not scraped.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
              <Label htmlFor="source">Source</Label>
              <select id="source" className={fieldClass} value={source}
                onChange={(event) => setSource(event.target.value as JobSource)}>
                <option value="arbeitnow">Arbeitnow</option>
                <option value="remotive">Remotive</option>
                <option value="eures">EURES (optional)</option>
                <option value="adzuna_nl">Adzuna NL (credentials required)</option>
              </select>
              <Label htmlFor="query">Keywords</Label>
              <Input id="query" value={query} onChange={(event) => setQuery(event.target.value)} />
              <Button disabled={loading} className="w-full" onClick={runImport}>Import up to 30</Button>
              <p className="text-xs text-slate-500">
                Automated risk checks reduce obvious fraud signals but cannot guarantee legitimacy.
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>3. Match and filter</CardTitle>
              <CardDescription>Salary means annual gross EUR. Unknown salaries are explicit.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
              <Label htmlFor="city">Dutch city</Label>
              <Input id="city" placeholder="Amsterdam" value={city}
                onChange={(event) => setCity(event.target.value)} />
              <Label htmlFor="salary">Minimum annual salary (€)</Label>
              <Input id="salary" type="number" min="0" placeholder="45000" value={minimumSalary}
                onChange={(event) => setMinimumSalary(event.target.value)} />
              <Label htmlFor="workplace">Workplace</Label>
              <select id="workplace" className={fieldClass} value={workplaceMode}
                onChange={(event) => setWorkplaceMode(event.target.value)}>
                <option value="">Any</option>
                <option value="onsite">On-site</option>
                <option value="hybrid">Hybrid</option>
                <option value="remote">Remote</option>
              </select>
              <Label htmlFor="limit">Maximum results</Label>
              <select id="limit" className={fieldClass} value={limit}
                onChange={(event) => setLimit(Number(event.target.value))}>
                <option value={10}>10</option>
                <option value={20}>20</option>
                <option value={30}>30</option>
              </select>
              <label className="flex items-center gap-2 text-sm">
                <input type="checkbox" checked={includeUnknownSalary}
                  onChange={(event) => setIncludeUnknownSalary(event.target.checked)} />
                Include jobs without published salary
              </label>
              <Button disabled={loading || !resume} className="w-full" onClick={runMatching}>
                Analyse best matches
              </Button>
            </CardContent>
          </Card>
        </aside>

        <section>
          <p className="text-sm font-semibold text-cyan-700">EVIDENCE-BASED MATCHING</p>
          <div className="mb-5 flex flex-wrap items-center justify-between gap-3">
            <h2 className="text-3xl font-bold">Best opportunities</h2>
            <Badge variant="secondary">{matches.length} jobs</Badge>
          </div>
          {message && <p className="mb-4 rounded-lg border bg-white p-3 text-sm">{message}</p>}
          {matches.length === 0 ? (
            <Card className="border-dashed py-12 text-center">
              <CardContent>
                <p className="font-semibold">No AI results yet.</p>
                <p className="mt-2 text-sm text-slate-500">
                  Upload your CV, import jobs, choose filters and start matching.
                </p>
              </CardContent>
            </Card>
          ) : matches.map((match) => (
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
                        {match.legitimacy_status === "source_verified" ? "Source verified" : "Review legitimacy"}
                      </Badge>
                    </div>
                    <h3 className="mt-3 text-xl font-bold">{match.job.title}</h3>
                    <p className="text-slate-600">{match.job.company} · {match.job.location}</p>
                    <p className="mt-1 text-sm font-medium">{salary(match)} · {match.job.workplace_mode ?? "Mode unknown"}</p>
                    <div className="mt-4 grid gap-3 text-sm md:grid-cols-2">
                      <div className="rounded-lg bg-emerald-50 p-3">
                        <strong>Strengths</strong>
                        <ul className="mt-1 list-disc pl-4">{match.strengths.map((item) => <li key={item}>{item}</li>)}</ul>
                      </div>
                      <div className="rounded-lg bg-amber-50 p-3">
                        <strong>Gaps to check</strong>
                        <ul className="mt-1 list-disc pl-4">{match.gaps.map((item) => <li key={item}>{item}</li>)}</ul>
                      </div>
                    </div>
                    {match.evidence.length > 0 && (
                      <details className="mt-3 text-sm">
                        <summary className="cursor-pointer font-semibold">Verbatim evidence</summary>
                        {match.evidence.map((item, index) => (
                          <p className="mt-2 border-l-2 border-cyan-600 pl-3" key={`${item.cv}-${index}`}>
                            CV: “{item.cv}”<br />Job: “{item.job}”
                          </p>
                        ))}
                      </details>
                    )}
                    {match.legitimacy_reasons.length > 0 && (
                      <p className="mt-3 text-xs text-slate-500">
                        Risk-screen notes: {match.legitimacy_reasons.join(", ")}. Verify on the employer website.
                      </p>
                    )}
                    {match.job.source_attribution && <p className="mt-2 text-xs text-slate-500">{match.job.source_attribution}</p>}
                  </div>
                  <div className="flex shrink-0 flex-col gap-2">
                    <Button render={<a href={match.job.url} target="_blank" rel="noreferrer" />}>View job</Button>
                    <select className={fieldClass} aria-label={`Application status for ${match.job.title}`}
                      value={applicationStatuses[match.job_id] ?? ""}
                      onChange={(event) => updateApplication(match.job_id, event.target.value as ApplicationStatus)}>
                      <option value="" disabled>Track status</option>
                      <option value="saved">Saved</option>
                      <option value="applied">Applied</option>
                      <option value="interview">Interview</option>
                      <option value="rejected">Rejected</option>
                      <option value="offer">Offer</option>
                      <option value="withdrawn">Withdrawn</option>
                    </select>
                    <Button variant="outline" onClick={() => showHousing(match)}>Housing options</Button>
                  </div>
                </div>

                {housing[match.job_id] && (
                  <div className="mt-5 rounded-xl border border-slate-200 bg-slate-50 p-4 text-sm">
                    <h4 className="font-bold">Housing around {housing[match.job_id].job_city}</h4>
                    {housing[match.job_id].affordability && (
                      <p className="mt-1">
                        Estimated range: €{housing[match.job_id].affordability.minimum_monthly_rent.toLocaleString()}–
                        €{housing[match.job_id].affordability.maximum_monthly_rent.toLocaleString()}/month
                      </p>
                    )}
                    <div className="mt-3 flex flex-wrap gap-3">
                      {housing[match.job_id].nearby_cities.map((item) => (
                        <div className="rounded-lg bg-white p-3" key={item.city}>
                          <strong>{item.city}</strong> <span className="text-slate-500">({item.relation})</span>
                          <div className="mt-1 flex gap-2">
                            {item.provider_links.map((link) => (
                              <a className="text-cyan-700 underline" href={link.url} target="_blank"
                                rel="noreferrer" key={link.provider}>{link.provider}</a>
                            ))}
                          </div>
                          <p className="mt-1 text-xs text-amber-700">Registration: verify manually</p>
                        </div>
                      ))}
                    </div>
                    <p className="mt-3 text-xs text-slate-500">
                      {housing[match.job_id].data_notice} {housing[match.job_id].guarantee_notice}
                    </p>
                  </div>
                )}
              </CardContent>
            </Card>
          ))}
        </section>
      </div>
    </main>
  );
}
