const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8100";

export type Profile = {
  id?: number;
  name: string;
  headline: string;
  skills: string[];
  desired_roles: string[];
  preferred_countries: string[];
};

export type Job = {
  id: number;
  source: string;
  external_id: string;
  title: string;
  company: string;
  country: string;
  location: string;
  description: string;
  url: string;
  employment_type: string;
  salary_min: number | null;
  salary_max: number | null;
  salary_currency: string | null;
  workplace_mode: "onsite" | "hybrid" | "remote" | null;
  legitimacy_status: "source_verified" | "needs_review" | "rejected";
  legitimacy_reasons: string[];
  source_attribution: string | null;
  created_at: string;
};

export type JobMatch = {
  job: Job;
  score: number;
  reasons: string[];
};

export type ResumeProfile = {
  id: number;
  user_id: number;
  target_roles: string[];
  skills: string[];
  experience_level: "entry" | "mid" | "senior" | "lead" | "executive" | null;
  years_experience: number | null;
  languages: string[];
  preferred_countries: string[];
  work_authorization: string[];
  summary: string | null;
  extracted_character_count: number;
  updated_at: string;
};

export type JobSource = "arbeitnow" | "remotive" | "eures" | "adzuna_nl";

export type JobImportResult = {
  source: JobSource;
  imported: number;
  duplicates: number;
  discarded: number;
  jobs: Job[];
  attribution: string | null;
  risk_notice: string;
};

export type AIMatch = {
  job_id: number;
  overall_score: number;
  recommendation: "apply" | "review" | "skip";
  strengths: string[];
  gaps: string[];
  evidence: { cv: string; job: string }[];
  job: Job;
  legitimacy_status: "source_verified" | "needs_review";
  legitimacy_reasons: string[];
  method: "ai" | "deterministic_demo";
};

export type MatchFilters = {
  country?: string;
  city?: string;
  minimum_salary?: number;
  include_unknown_salary: boolean;
  workplace_mode?: "onsite" | "hybrid" | "remote";
  limit: number;
};

export type ApplicationStatus =
  | "saved"
  | "applied"
  | "interview"
  | "rejected"
  | "offer"
  | "withdrawn";

export type JobApplication = {
  id: number;
  user_id: number;
  job_id: number;
  status: ApplicationStatus;
  notes: string | null;
  created_at: string;
  updated_at: string;
  job: Job;
};

export type HousingAssistance = {
  job_city: string;
  nearby_cities: {
    city: string;
    relation: string;
    registration_status: "unknown";
    provider_links: {
      provider: "Funda" | "Pararius" | "Kamernet";
      url: string;
      relationship: "provider_search_link";
    }[];
  }[];
  affordability: {
    minimum_monthly_rent: number;
    maximum_monthly_rent: number;
    label: "estimate";
    basis: string;
  } | null;
  manual_verification_checklist: string[];
  guarantee_notice: string;
  data_notice: string;
};

async function request<T>(path: string, options: RequestInit = {}, token?: string): Promise<T> {
  const isFormData = options.body instanceof FormData;
  const response = await fetch(`${API_URL}${path}`, {
    ...options,
    headers: {
      ...(!isFormData ? { "Content-Type": "application/json" } : {}),
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...options.headers,
    },
  });

  if (!response.ok) {
    const body = await response.json().catch(() => ({ detail: "Unexpected server response" }));
    throw new Error(typeof body.detail === "string" ? body.detail : "Request failed");
  }
  return response.json() as Promise<T>;
}

export async function authenticate(email: string, password: string, register: boolean) {
  return request<{ access_token: string }>(`/api/auth/${register ? "register" : "login"}`, {
    method: "POST",
    body: JSON.stringify({ email, password }),
  });
}

export const getProfile = (token: string) => request<Profile>("/api/profile", {}, token);

export const saveProfile = (token: string, profile: Profile) =>
  request<Profile>(
    "/api/profile",
    { method: "PUT", body: JSON.stringify(profile) },
    token,
  );

export const getMatches = (token: string) => request<JobMatch[]>("/api/matches", {}, token);

export const getResume = (token: string) => request<ResumeProfile>("/api/resume", {}, token);

export const uploadResume = (token: string, file: File) => {
  const body = new FormData();
  body.append("file", file);
  return request<ResumeProfile>("/api/resume", { method: "POST", body }, token);
};

export const importJobs = (
  token: string,
  payload: { source: JobSource; query: string; country: string; limit: number },
) =>
  request<JobImportResult>(
    "/api/jobs/import",
    { method: "POST", body: JSON.stringify(payload) },
    token,
  );

export const getAIMatches = (token: string, filters: MatchFilters) =>
  request<AIMatch[]>(
    "/api/matches/ai",
    { method: "POST", body: JSON.stringify(filters) },
    token,
  );

export const getApplications = (token: string) =>
  request<JobApplication[]>("/api/applications", {}, token);

export const saveApplication = (
  token: string,
  jobId: number,
  status: ApplicationStatus,
  notes?: string,
) =>
  request<JobApplication>(
    `/api/applications/${jobId}`,
    { method: "PUT", body: JSON.stringify({ status, notes }) },
    token,
  );

export const getHousingAssistance = (
  token: string,
  payload: { job_city: string; annual_gross_salary?: number; max_monthly_rent?: number },
) =>
  request<HousingAssistance>(
    "/api/housing/assistance",
    { method: "POST", body: JSON.stringify(payload) },
    token,
  );
