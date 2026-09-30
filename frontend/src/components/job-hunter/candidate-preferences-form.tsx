"use client";

import { FormEvent, useState } from "react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { CandidatePreferences } from "@/lib/api";

const CITIES = [
  "Amsterdam",
  "Utrecht",
  "Den Haag",
  "Haarlem",
  "Almere",
  "Middelburg",
  "Eindhoven",
  "Rotterdam",
] as const;

export const BLANK_PREFERENCES: CandidatePreferences = {
  target_roles: [],
  experience_level: "junior",
  skills: [],
  job_types: ["technology"],
  preferred_cities: ["Amsterdam"],
  workplace_modes: ["onsite", "hybrid", "remote"],
  schedules: ["full_time"],
  minimum_salary_gross_annual: null,
  available_from: null,
  lives_in_netherlands: false,
  needs_relocation: true,
  dutch_level: "none",
  english_level: "b2",
  work_authorization: "eu_citizen",
  sponsorship_required: false,
  onboarding_complete: true,
};

const splitItems = (value: string) =>
  value.split(",").map((item) => item.trim()).filter(Boolean);

type ArrayField = "job_types" | "preferred_cities" | "workplace_modes" | "schedules";

type CandidatePreferencesFormProps = {
  initialValue?: CandidatePreferences | null;
  loading?: boolean;
  onComplete: (preferences: CandidatePreferences) => Promise<void>;
};

export function CandidatePreferencesForm({
  initialValue,
  loading = false,
  onComplete,
}: CandidatePreferencesFormProps) {
  const [step, setStep] = useState(1);
  const [value, setValue] = useState<CandidatePreferences>(
    initialValue ?? BLANK_PREFERENCES,
  );
  const [error, setError] = useState("");

  function toggleArrayValue(field: ArrayField, item: string) {
    setValue((current) => {
      const values = current[field] as string[];
      const next = values.includes(item)
        ? values.filter((valueItem) => valueItem !== item)
        : [...values, item];
      return { ...current, [field]: next };
    });
  }

  function validateCurrentStep() {
    if (step === 1 && value.target_roles.length === 0) {
      return "Add at least one target role.";
    }
    if (step === 1 && value.job_types.length === 0) {
      return "Choose at least one type of work.";
    }
    if (step === 2 && value.preferred_cities.length === 0) {
      return "Choose at least one Dutch city.";
    }
    if (step === 2 && value.workplace_modes.length === 0) {
      return "Choose at least one workplace mode.";
    }
    if (step === 2 && value.schedules.length === 0) {
      return "Choose at least one schedule.";
    }
    return "";
  }

  function nextStep() {
    const validationError = validateCurrentStep();
    setError(validationError);
    if (!validationError) setStep((current) => Math.min(3, current + 1));
  }

  async function submit(event: FormEvent) {
    event.preventDefault();
    const validationError = validateCurrentStep();
    setError(validationError);
    if (validationError) return;
    try {
      await onComplete(value);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Could not save your preferences.");
    }
  }

  return (
    <form onSubmit={submit} noValidate>
      <div className="mb-6 flex items-center justify-between gap-4">
        <div>
          <p className="text-sm font-bold text-cyan-800">Step {step} of 3</p>
          <h2 className="text-2xl font-bold">
            {step === 1 ? "Professional profile" : step === 2 ? "Job preferences" : "Your situation"}
          </h2>
        </div>
        <div aria-hidden="true" className="flex gap-2">
          {[1, 2, 3].map((number) => (
            <span
              className={`h-2 w-10 rounded-full ${number <= step ? "bg-cyan-800" : "bg-slate-200"}`}
              key={number}
            />
          ))}
        </div>
      </div>

      {step === 1 && (
        <div className="space-y-5">
          <div>
            <Label htmlFor="target-roles">Target roles</Label>
            <Input
              id="target-roles"
              className="mt-2 min-h-11"
              required
              aria-describedby="target-roles-help"
              placeholder="Junior Python Developer, Cook, Warehouse Worker"
              value={value.target_roles.join(", ")}
              onChange={(event) => {
                setValue({ ...value, target_roles: splitItems(event.target.value) });
              }}
            />
            <p id="target-roles-help" className="mt-1 text-sm text-slate-600">
              Separate multiple roles with commas.
            </p>
          </div>
          <div>
            <Label htmlFor="experience-level">Experience level</Label>
            <select
              id="experience-level"
              className="mt-2 min-h-11 w-full rounded-lg border border-slate-300 bg-white px-3 text-base"
              value={value.experience_level}
              onChange={(event) => {
                setValue({
                  ...value,
                  experience_level: event.target.value as CandidatePreferences["experience_level"],
                });
              }}
            >
              <option value="no_experience">No experience</option>
              <option value="junior">Junior</option>
              <option value="mid">Mid-level</option>
              <option value="senior">Senior</option>
              <option value="lead">Lead</option>
            </select>
          </div>
          <div>
            <Label htmlFor="skills">Skills and technologies</Label>
            <Input
              id="skills"
              className="mt-2 min-h-11"
              placeholder="Python, FastAPI, customer service"
              value={value.skills.join(", ")}
              onChange={(event) => setValue({ ...value, skills: splitItems(event.target.value) })}
            />
          </div>
          <fieldset>
            <legend className="text-sm font-medium">Types of work</legend>
            <div className="mt-2 grid gap-2 sm:grid-cols-2">
              {[
                ["technology", "Technology"],
                ["human_resources", "Human resources"],
                ["hospitality", "Hospitality"],
                ["logistics", "Logistics / warehouse"],
                ["other", "Other"],
              ].map(([id, label]) => (
                <label className="flex min-h-11 items-center gap-3 rounded-lg border p-3" key={id}>
                  <input
                    type="checkbox"
                    checked={value.job_types.includes(id as CandidatePreferences["job_types"][number])}
                    onChange={() => toggleArrayValue("job_types", id)}
                  />
                  {label}
                </label>
              ))}
            </div>
          </fieldset>
        </div>
      )}

      {step === 2 && (
        <div className="space-y-5">
          <fieldset>
            <legend className="text-sm font-medium">Preferred cities or regions</legend>
            <div className="mt-2 grid gap-2 sm:grid-cols-2">
              {CITIES.map((city) => (
                <label className="flex min-h-11 items-center gap-3 rounded-lg border p-3" key={city}>
                  <input
                    type="checkbox"
                    checked={value.preferred_cities.includes(city)}
                    onChange={() => toggleArrayValue("preferred_cities", city)}
                  />
                  {city}
                </label>
              ))}
            </div>
          </fieldset>
          <fieldset>
            <legend className="text-sm font-medium">Workplace mode</legend>
            <div className="mt-2 flex flex-wrap gap-2">
              {[
                ["onsite", "On-site"],
                ["hybrid", "Hybrid"],
                ["remote", "Remote"],
              ].map(([id, label]) => (
                <label className="flex min-h-11 items-center gap-2 rounded-lg border px-3" key={id}>
                  <input
                    type="checkbox"
                    checked={value.workplace_modes.includes(
                      id as CandidatePreferences["workplace_modes"][number],
                    )}
                    onChange={() => toggleArrayValue("workplace_modes", id)}
                  />
                  {label}
                </label>
              ))}
            </div>
          </fieldset>
          <fieldset>
            <legend className="text-sm font-medium">Schedule and contract preference</legend>
            <div className="mt-2 grid gap-2 sm:grid-cols-2">
              {[
                ["full_time", "Full-time"],
                ["part_time", "Part-time"],
                ["temporary", "Temporary"],
                ["internship", "Internship"],
                ["freelance", "Freelance"],
              ].map(([id, label]) => (
                <label className="flex min-h-11 items-center gap-3 rounded-lg border p-3" key={id}>
                  <input
                    type="checkbox"
                    checked={value.schedules.includes(id as CandidatePreferences["schedules"][number])}
                    onChange={() => toggleArrayValue("schedules", id)}
                  />
                  {label}
                </label>
              ))}
            </div>
          </fieldset>
          <div className="grid gap-4 sm:grid-cols-2">
            <div>
              <Label htmlFor="minimum-salary">Minimum annual gross salary (€)</Label>
              <Input
                id="minimum-salary"
                className="mt-2 min-h-11"
                type="number"
                min="0"
                value={value.minimum_salary_gross_annual ?? ""}
                onChange={(event) => {
                  setValue({
                    ...value,
                    minimum_salary_gross_annual: event.target.value
                      ? Number(event.target.value)
                      : null,
                  });
                }}
              />
            </div>
            <div>
              <Label htmlFor="available-from">Available from</Label>
              <Input
                id="available-from"
                className="mt-2 min-h-11"
                type="date"
                value={value.available_from ?? ""}
                onChange={(event) => {
                  setValue({ ...value, available_from: event.target.value || null });
                }}
              />
            </div>
          </div>
        </div>
      )}

      {step === 3 && (
        <div className="space-y-5">
          <div className="grid gap-4 sm:grid-cols-2">
            <div>
              <Label htmlFor="lives-nl">Do you currently live in the Netherlands?</Label>
              <select
                id="lives-nl"
                className="mt-2 min-h-11 w-full rounded-lg border border-slate-300 bg-white px-3 text-base"
                value={value.lives_in_netherlands ? "yes" : "no"}
                onChange={(event) => {
                  setValue({ ...value, lives_in_netherlands: event.target.value === "yes" });
                }}
              >
                <option value="no">No</option>
                <option value="yes">Yes</option>
              </select>
            </div>
            <div>
              <Label htmlFor="relocation">Do you need relocation help?</Label>
              <select
                id="relocation"
                className="mt-2 min-h-11 w-full rounded-lg border border-slate-300 bg-white px-3 text-base"
                value={value.needs_relocation ? "yes" : "no"}
                onChange={(event) => {
                  setValue({ ...value, needs_relocation: event.target.value === "yes" });
                }}
              >
                <option value="yes">Yes</option>
                <option value="no">No</option>
              </select>
            </div>
            {(["dutch_level", "english_level"] as const).map((field) => (
              <div key={field}>
                <Label htmlFor={field}>{field === "dutch_level" ? "Dutch level" : "English level"}</Label>
                <select
                  id={field}
                  className="mt-2 min-h-11 w-full rounded-lg border border-slate-300 bg-white px-3 text-base"
                  value={value[field]}
                  onChange={(event) => {
                    setValue({
                      ...value,
                      [field]: event.target.value as CandidatePreferences[typeof field],
                    });
                  }}
                >
                  <option value="none">None</option>
                  {["a1", "a2", "b1", "b2", "c1", "c2"].map((level) => (
                    <option value={level} key={level}>{level.toUpperCase()}</option>
                  ))}
                  <option value="native">Native</option>
                </select>
              </div>
            ))}
            <div>
              <Label htmlFor="work-authorization">Right to work in the Netherlands</Label>
              <select
                id="work-authorization"
                className="mt-2 min-h-11 w-full rounded-lg border border-slate-300 bg-white px-3 text-base"
                value={value.work_authorization}
                onChange={(event) => {
                  setValue({
                    ...value,
                    work_authorization: event.target.value as CandidatePreferences["work_authorization"],
                  });
                }}
              >
                <option value="eu_citizen">EU citizen</option>
                <option value="permit">I have a permit</option>
                <option value="requires_visa">I require a visa</option>
                <option value="unknown">I am not sure</option>
              </select>
            </div>
            <label className="flex min-h-11 items-center gap-3 self-end rounded-lg border p-3">
              <input
                type="checkbox"
                checked={value.sponsorship_required}
                onChange={(event) => {
                  setValue({ ...value, sponsorship_required: event.target.checked });
                }}
              />
              I need employer sponsorship
            </label>
          </div>

          <div className="rounded-xl bg-slate-50 p-4">
            <div className="mb-3 flex items-center gap-2">
              <Badge>Review</Badge>
              <h3 className="font-bold">Before saving</h3>
            </div>
            <dl className="grid gap-2 text-sm sm:grid-cols-2">
              <div><dt className="font-semibold">Roles</dt><dd>{value.target_roles.join(", ")}</dd></div>
              <div><dt className="font-semibold">Cities</dt><dd>{value.preferred_cities.join(", ")}</dd></div>
              <div><dt className="font-semibold">Work modes</dt><dd>{value.workplace_modes.join(", ")}</dd></div>
              <div><dt className="font-semibold">Languages</dt><dd>NL {value.dutch_level.toUpperCase()} · EN {value.english_level.toUpperCase()}</dd></div>
            </dl>
          </div>
        </div>
      )}

      {error && (
        <p id="onboarding-error" role="alert" className="mt-5 rounded-lg bg-red-50 p-3 text-sm text-red-800">
          {error}
        </p>
      )}

      <div className="mt-6 flex flex-wrap justify-between gap-3">
        <Button
          type="button"
          variant="outline"
          className="min-h-11"
          disabled={step === 1 || loading}
          onClick={() => {
            setError("");
            setStep((current) => Math.max(1, current - 1));
          }}
        >
          Back
        </Button>
        {step < 3 ? (
          <Button type="button" className="min-h-11" disabled={loading} onClick={nextStep}>
            Continue
          </Button>
        ) : (
          <Button type="submit" className="min-h-11" disabled={loading}>
            {loading ? "Saving…" : "Save and go to Today"}
          </Button>
        )}
      </div>
    </form>
  );
}
