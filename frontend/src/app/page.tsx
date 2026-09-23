"use client";

import { FormEvent, useEffect, useState } from "react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { authenticate, getMatches, getProfile, JobMatch, Profile, saveProfile } from "@/lib/api";

const blankProfile: Profile = {
  name: "",
  headline: "",
  skills: [],
  desired_roles: [],
  preferred_countries: [],
};

const split = (value: string) => value.split(",").map((item) => item.trim()).filter(Boolean);

export default function Home() {
  const [token, setToken] = useState<string | null>(null);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [register, setRegister] = useState(false);
  const [profile, setProfile] = useState<Profile>(blankProfile);
  const [matches, setMatches] = useState<JobMatch[]>([]);
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const frame = requestAnimationFrame(() => {
      setToken(sessionStorage.getItem("job-hunter-token"));
    });
    return () => cancelAnimationFrame(frame);
  }, []);

  async function load(accessToken: string) {
    try {
      setProfile(await getProfile(accessToken));
      setMatches(await getMatches(accessToken));
    } catch (error) {
      if (error instanceof Error && error.message !== "Profile not created") {
        setMessage(error.message);
      }
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
      await load(result.access_token);
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "No se pudo completar el acceso");
    } finally {
      setLoading(false);
    }
  }

  async function submitProfile(event: FormEvent) {
    event.preventDefault();
    if (!token) return;
    setLoading(true);
    setMessage("");
    try {
      setProfile(await saveProfile(token, profile));
      setMatches(await getMatches(token));
      setMessage("Perfil guardado y ofertas recalculadas.");
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "No se pudo guardar el perfil");
    } finally {
      setLoading(false);
    }
  }

  if (!token) {
    return (
      <main className="grid min-h-screen bg-slate-950 px-5 py-10 text-slate-100 lg:grid-cols-2 lg:items-center lg:px-20">
        <section className="mx-auto max-w-xl py-12">
          <Badge className="mb-6 bg-cyan-400 text-slate-950">EUROPEAN CAREER COPILOT</Badge>
          <h1 className="text-5xl font-black leading-tight tracking-tight md:text-7xl">
            Encuentra el puesto que encaja contigo.
          </h1>
          <p className="mt-6 max-w-lg text-lg text-slate-300">
            Centraliza ofertas europeas y entiende por qué cada oportunidad merece tu atención.
          </p>
        </section>
        <Card className="mx-auto w-full max-w-md border-slate-700 bg-slate-900 text-slate-100">
          <CardHeader>
            <CardTitle>{register ? "Crea tu cuenta" : "Accede a tu espacio"}</CardTitle>
            <CardDescription className="text-slate-400">
              Tu perfil y recomendaciones permanecen separados.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form className="space-y-5" onSubmit={submitAuth}>
              <Label htmlFor="email">Email</Label>
              <Input id="email" type="email" required value={email}
                className="border-slate-700 bg-slate-950 text-slate-100"
                onChange={(event) => setEmail(event.target.value)} />
              <Label htmlFor="password">Contraseña</Label>
              <Input id="password" type="password" required minLength={register ? 10 : undefined}
                className="border-slate-700 bg-slate-950 text-slate-100"
                value={password} onChange={(event) => setPassword(event.target.value)} />
              {message && <p className="text-sm text-amber-300">{message}</p>}
              <Button disabled={loading} className="w-full bg-cyan-400 text-slate-950">
                {loading ? "Procesando…" : register ? "Crear cuenta" : "Entrar"}
              </Button>
              <Button type="button" variant="ghost" className="w-full"
                onClick={() => setRegister((current) => !current)}>
                {register ? "Ya tengo cuenta" : "Crear una cuenta"}
              </Button>
            </form>
          </CardContent>
        </Card>
      </main>
    );
  }

  return (
    <main className="min-h-screen bg-slate-100 text-slate-950">
      <header className="border-b bg-slate-950 px-5 py-5 text-white">
        <div className="mx-auto flex max-w-6xl items-center justify-between">
          <div>
            <p className="text-xs font-bold tracking-[.25em] text-cyan-400">AI JOB HUNTER</p>
            <h1 className="text-xl font-semibold">Panel de oportunidades</h1>
          </div>
          <Button variant="outline" onClick={() => {
            sessionStorage.removeItem("job-hunter-token");
            setToken(null);
          }}>Cerrar sesión</Button>
        </div>
      </header>
      <div className="mx-auto grid max-w-6xl gap-6 px-5 py-8 lg:grid-cols-[380px_1fr]">
        <Card className="h-fit">
          <CardHeader>
            <CardTitle>Tu perfil profesional</CardTitle>
            <CardDescription>Separa skills, roles y países con comas.</CardDescription>
          </CardHeader>
          <CardContent>
            <form className="space-y-4" onSubmit={submitProfile}>
              <Label htmlFor="name">Nombre</Label>
              <Input id="name" required value={profile.name}
                onChange={(event) => setProfile({ ...profile, name: event.target.value })} />
              <Label htmlFor="headline">Titular</Label>
              <Input id="headline" value={profile.headline}
                onChange={(event) => setProfile({ ...profile, headline: event.target.value })} />
              {([
                ["Skills", "skills"],
                ["Roles deseados", "desired_roles"],
                ["Países preferidos", "preferred_countries"],
              ] as const).map(([label, key]) => (
                <div className="space-y-2" key={key}>
                  <Label htmlFor={key}>{label}</Label>
                  <Input id={key} value={profile[key].join(", ")}
                    onChange={(event) => setProfile({ ...profile, [key]: split(event.target.value) })} />
                </div>
              ))}
              <Button disabled={loading} className="w-full">Guardar y recalcular</Button>
              {message && <p className="text-sm text-slate-600">{message}</p>}
            </form>
          </CardContent>
        </Card>
        <section>
          <p className="text-sm font-semibold text-cyan-700">MATCHING PERSONALIZADO</p>
          <div className="mb-5 flex items-center justify-between">
            <h2 className="text-3xl font-bold">Mejores oportunidades</h2>
            <Badge variant="secondary">{matches.length} ofertas</Badge>
          </div>
          {matches.length === 0 ? (
            <Card className="border-dashed py-12 text-center">
              <CardContent>
                <p className="font-semibold">Todavía no hay ofertas para comparar.</p>
                <p className="mt-2 text-sm text-slate-500">
                  Completa tu perfil. Los conectores autorizados llegarán en la siguiente fase.
                </p>
              </CardContent>
            </Card>
          ) : matches.map(({ job, score, reasons }) => (
            <Card className="mb-4" key={job.id}>
              <CardContent className="flex flex-col gap-5 pt-6 sm:flex-row">
                <div className="grid h-16 w-16 shrink-0 place-items-center rounded-2xl bg-slate-950 text-xl font-black text-cyan-400">
                  {score}%
                </div>
                <div className="flex-1">
                  <Badge variant="outline">{job.source} · {job.country}</Badge>
                  <h3 className="mt-3 text-xl font-bold">{job.title}</h3>
                  <p className="text-slate-600">{job.company} · {job.location}</p>
                  <p className="mt-3 text-sm text-slate-500">{reasons.join(" · ")}</p>
                </div>
                <Button render={<a href={job.url} target="_blank" rel="noreferrer" />}>
                  Ver oferta
                </Button>
              </CardContent>
            </Card>
          ))}
        </section>
      </div>
    </main>
  );
}
