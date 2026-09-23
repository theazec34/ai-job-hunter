const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

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
  created_at: string;
};

export type JobMatch = {
  job: Job;
  score: number;
  reasons: string[];
};

async function request<T>(path: string, options: RequestInit = {}, token?: string): Promise<T> {
  const response = await fetch(`${API_URL}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
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
