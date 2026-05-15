"use client";

import { useState, type FormEvent } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? "";

export function LoginForm() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      const res = await fetch(`${API_BASE}/api/auth/login`, {
        method: "POST",
        credentials: "include",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, password }),
      });
      if (!res.ok) {
        const body = await res.json().catch(() => null);
        throw new Error(body?.detail ?? `Errore ${res.status}`);
      }
      window.location.href = "/dashboard";
    } catch (err) {
      setError(err instanceof Error ? err.message : "Errore di login");
      setSubmitting(false);
    }
  }

  return (
    <form onSubmit={onSubmit} className="rounded-2xl border border-[color:var(--color-line)] bg-[color:var(--color-bg-soft)] p-6 space-y-4">
      <div className="space-y-1.5">
        <label htmlFor="username" className="text-xs uppercase tracking-wider text-[color:var(--color-text-muted)]">Username</label>
        <Input
          id="username"
          autoComplete="username"
          required
          value={username}
          onChange={e => setUsername(e.target.value)}
          disabled={submitting}
        />
      </div>
      <div className="space-y-1.5">
        <label htmlFor="password" className="text-xs uppercase tracking-wider text-[color:var(--color-text-muted)]">Password</label>
        <Input
          id="password"
          type="password"
          autoComplete="current-password"
          required
          value={password}
          onChange={e => setPassword(e.target.value)}
          disabled={submitting}
        />
      </div>
      {error && (
        <div className="rounded-lg border border-[color:var(--color-danger)]/30 bg-[color:var(--color-danger)]/10 px-3 py-2 text-xs text-[color:var(--color-danger)]">
          {error}
        </div>
      )}
      <Button type="submit" size="lg" className="w-full" disabled={submitting}>
        {submitting ? "Accesso…" : "Entra"}
      </Button>
    </form>
  );
}
