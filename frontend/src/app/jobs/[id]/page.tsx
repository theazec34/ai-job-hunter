"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { getJob, Job, saveApplication } from "@/lib/api";

function salary(job: Job) {
  if (job.salary_min === null && job.salary_max === null) return "Not published";
  const values = [job.salary_min, job.salary_max].filter((value) => value !== null);
  return `${job.salary_currency ?? ""} ${values.map((value) => value?.toLocaleString()).join("–")}`;
}

export default function JobDetailPage() {
  const params = useParams<{ id: string }>();
  const router = useRouter();
  const [job, setJob] = useState<Job | null>(null);
  const [status, setStatus] = useState<"idle" | "loading" | "ready" | "error">("loading");
  const [applicationState, setApplicationState] = useState<"none" | "saved" | "applied">("none");
  const [error, setError] = useState("");

  useEffect(() => {
    const frame = requestAnimationFrame(() => {
      const token = sessionStorage.getItem("job-hunter-token");
      const jobId = Number(params.id);
      if (!token) {
        router.replace("/");
        return;
      }
      if (!Number.isInteger(jobId) || jobId <= 0) {
        setError("This job reference is invalid.");
        setStatus("error");
        return;
      }
      void getJob(token, jobId)
        .then((result) => {
          setJob(result);
          setStatus("ready");
        })
        .catch((caught: unknown) => {
          setError(caught instanceof Error ? caught.message : "Could not load this job.");
          setStatus("error");
        });
    });
    return () => cancelAnimationFrame(frame);
  }, [params.id, router]);

  async function track(nextStatus: "saved" | "applied") {
    const token = sessionStorage.getItem("job-hunter-token");
    if (!token || !job) return;
    try {
      await saveApplication(token, job.id, nextStatus);
      setApplicationState(nextStatus);
      if (nextStatus === "applied") {
        window.open(job.url, "_blank", "noopener,noreferrer");
      }
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Could not update this application.");
    }
  }

  if (status === "loading") {
    return (
      <main className="grid min-h-screen place-items-center bg-slate-50 p-6">
        <p role="status" className="text-slate-700">Loading job details…</p>
      </main>
    );
  }

  if (status === "error" || !job) {
    return (
      <main className="grid min-h-screen place-items-center bg-slate-50 p-6">
        <Card className="max-w-lg">
          <CardContent className="pt-6 text-center">
            <h1 className="text-xl font-bold">Job unavailable</h1>
            <p role="alert" className="mt-2 text-slate-700">{error}</p>
            <Button className="mt-5 min-h-11" onClick={() => router.push("/")}>Back to Today</Button>
          </CardContent>
        </Card>
      </main>
    );
  }

  return (
    <main className="min-h-screen bg-slate-50 pb-24 text-slate-950 md:pb-10">
      <header className="border-b border-slate-200 bg-white px-4 py-4">
        <div className="mx-auto max-w-5xl">
          <Button className="min-h-11" variant="outline" onClick={() => router.back()}>
            Back
          </Button>
        </div>
      </header>
      <article className="mx-auto max-w-5xl px-4 py-8">
        <div className="flex flex-col gap-6 md:flex-row md:items-start">
          <div className="min-w-0 flex-1">
            <div className="flex flex-wrap gap-2">
              <Badge variant="outline">{job.source}</Badge>
              <Badge variant="secondary">{job.legitimacy_status.replace("_", " ")}</Badge>
            </div>
            <h1 className="mt-4 text-3xl font-black tracking-tight md:text-4xl">{job.title}</h1>
            <p className="mt-2 text-lg text-slate-700">{job.company} · {job.location}</p>
          </div>
          <div className="hidden shrink-0 gap-2 md:flex">
            <Button className="min-h-11" onClick={() => { void track("applied"); }}>
              {applicationState === "applied" ? "Application started" : "Apply"}
            </Button>
            <Button className="min-h-11" variant="outline"
              onClick={() => { void track("saved"); }}>
              {applicationState === "saved" ? "Saved" : "Save"}
            </Button>
          </div>
        </div>

        {error && <p role="alert" className="mt-5 rounded-lg bg-red-50 p-3 text-red-800">{error}</p>}

        <dl className="mt-8 grid gap-4 rounded-xl border border-slate-200 bg-white p-5 sm:grid-cols-2 lg:grid-cols-4">
          <div><dt className="text-sm font-semibold text-slate-600">Location</dt><dd>{job.location}</dd></div>
          <div><dt className="text-sm font-semibold text-slate-600">Work mode</dt><dd>{job.workplace_mode ?? "Not provided"}</dd></div>
          <div><dt className="text-sm font-semibold text-slate-600">Salary</dt><dd>{salary(job)}</dd></div>
          <div><dt className="text-sm font-semibold text-slate-600">Contract</dt><dd>{job.employment_type || "Not provided"}</dd></div>
          <div><dt className="text-sm font-semibold text-slate-600">Experience</dt><dd>Not provided</dd></div>
          <div><dt className="text-sm font-semibold text-slate-600">Languages</dt><dd>Not provided</dd></div>
          <div><dt className="text-sm font-semibold text-slate-600">Relocation</dt><dd>Not provided</dd></div>
          <div><dt className="text-sm font-semibold text-slate-600">Sponsorship</dt><dd>Not provided</dd></div>
        </dl>

        <section className="mt-8" aria-labelledby="description-title">
          <h2 id="description-title" className="text-2xl font-bold">Job description</h2>
          <p className="mt-4 whitespace-pre-line leading-7 text-slate-700">{job.description}</p>
        </section>

        <p className="mt-8 text-sm text-slate-600">
          Missing details are deliberately labelled “Not provided”. Always verify the original
          vacancy and employer before sharing personal information.
        </p>
      </article>

      <div className="fixed inset-x-0 bottom-0 z-40 flex gap-2 border-t border-slate-200 bg-white p-3 pb-[calc(.75rem+env(safe-area-inset-bottom))] md:hidden">
        <Button className="min-h-11 flex-1" onClick={() => { void track("applied"); }}>
          {applicationState === "applied" ? "Application started" : "Apply"}
        </Button>
        <Button className="min-h-11" variant="outline" onClick={() => { void track("saved"); }}>
          {applicationState === "saved" ? "Saved" : "Save"}
        </Button>
      </div>
    </main>
  );
}
