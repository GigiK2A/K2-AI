"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { useKbotAuth } from "@/app/providers";
import { fetchUserSessions, type DashboardPayload, type KbotSession } from "@/lib/api";

export default function DashboardPage() {
  const { user, isSignedIn, hasPaid, loading: authLoading, getToken } = useKbotAuth();
  const [data, setData] = useState<DashboardPayload | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!isSignedIn) return;
    let mounted = true;
    setLoading(true);
    (async () => {
      try {
        const token = await getToken();
        if (!token) throw new Error("Sessione di autenticazione non disponibile");
        const payload = await fetchUserSessions(token);
        if (mounted) setData(payload);
      } catch (e) {
        if (mounted) setError(e instanceof Error ? e.message : "Errore caricamento");
      } finally {
        if (mounted) setLoading(false);
      }
    })();
    return () => {
      mounted = false;
    };
  }, [getToken, isSignedIn]);

  if (authLoading) {
    return (
      <main className="flex min-h-screen items-center justify-center bg-[#050505] text-sm text-[#6b7280]">
        Caricamento…
      </main>
    );
  }

  if (!isSignedIn) {
    return (
      <main className="flex min-h-screen items-center justify-center bg-[#050505] px-6 text-white">
        <div className="max-w-md rounded-2xl border border-[#111] bg-[#0a0a0a] p-8 text-center">
          <h1 className="text-xl font-bold">Accedi per vedere il tuo account</h1>
          <Link
            href="/sign-in"
            className="mt-6 inline-flex rounded-lg bg-[var(--teal)] px-4 py-2 text-sm font-semibold text-black"
          >
            Accedi
          </Link>
        </div>
      </main>
    );
  }

  return (
    <main className="min-h-screen bg-[#050505] px-6 py-10 text-white">
      <div className="mx-auto max-w-4xl">
        <header className="mb-8 flex flex-wrap items-baseline justify-between gap-3">
          <h1 className="text-2xl font-bold">Account · K2-AI</h1>
          <Link href="/" className="text-sm text-[var(--teal)] hover:underline">
            ← Torna alla chat
          </Link>
        </header>

        <section className="mb-8 grid gap-4 md:grid-cols-3">
          <StatCard label="Email" value={user?.email ?? "—"} />
          <StatCard label="Piano" value={hasPaid ? "Premium" : "Free"} accent={hasPaid} />
          <StatCard
            label="Report generati"
            value={data ? String(data.stats.with_pdf) : "…"}
            sub={data ? `${data.stats.total} sessioni totali` : undefined}
          />
        </section>

        <section>
          <h2 className="mb-4 text-sm font-semibold uppercase tracking-wider text-[#9ca3af]">
            Le tue sessioni
          </h2>

          {loading && <p className="text-sm text-[#6b7280]">Caricamento sessioni…</p>}
          {error && <p className="text-sm text-red-300">{error}</p>}

          {!loading && data && data.sessions.length === 0 && (
            <div className="rounded-2xl border border-[#111] bg-[#0a0a0a] p-8 text-center">
              <p className="text-sm text-[#9ca3af]">
                Non hai ancora avviato nessuna conversazione.
              </p>
              <Link
                href="/"
                className="mt-4 inline-flex rounded-lg bg-[var(--teal)] px-4 py-2 text-sm font-semibold text-black"
              >
                Inizia ora →
              </Link>
            </div>
          )}

          {data && data.sessions.length > 0 && (
            <ul className="space-y-3">
              {data.sessions.map((s) => (
                <SessionRow key={s.id} session={s} />
              ))}
            </ul>
          )}
        </section>
      </div>
    </main>
  );
}

function StatCard({
  label,
  value,
  sub,
  accent,
}: {
  label: string;
  value: string;
  sub?: string;
  accent?: boolean;
}) {
  return (
    <div
      className={`rounded-2xl border bg-[#0a0a0a] p-5 ${
        accent ? "border-[var(--teal)]" : "border-[#111]"
      }`}
    >
      <p className="text-xs uppercase tracking-wider text-[#6b7280]">{label}</p>
      <p className={`mt-2 text-lg font-semibold ${accent ? "text-[var(--teal)]" : ""}`}>
        {value}
      </p>
      {sub && <p className="mt-1 text-xs text-[#6b7280]">{sub}</p>}
    </div>
  );
}

function SessionRow({ session }: { session: KbotSession }) {
  const created = new Date(session.timestamps.createdAt);
  const date = created.toLocaleDateString("it-IT", {
    day: "2-digit",
    month: "short",
    year: "numeric",
  });
  const time = created.toLocaleTimeString("it-IT", { hour: "2-digit", minute: "2-digit" });
  const lastUserMsg =
    [...(session.messages ?? [])].reverse().find((m) => m.role === "user")?.content ?? "—";

  return (
    <li className="rounded-2xl border border-[#111] bg-[#0a0a0a] p-5">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="min-w-0 flex-1">
          <p className="truncate text-sm font-medium">
            {session.summary || lastUserMsg || `Sessione ${session.id.slice(0, 8)}`}
          </p>
          <p className="mt-1 text-xs text-[#6b7280]">
            {date} · {time} · {session.serviceId ?? "—"}
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <StatusPill status={session.status} hasPdf={Boolean(session.pdfUrl)} />
          {session.pdfUrl && (
            <a
              href={session.pdfUrl}
              target="_blank"
              rel="noreferrer"
              className="rounded-lg bg-[var(--teal)] px-3 py-1.5 text-xs font-semibold text-black"
            >
              Apri PDF
            </a>
          )}
        </div>
      </div>
    </li>
  );
}

function StatusPill({ status, hasPdf }: { status: string | null; hasPdf: boolean }) {
  let label = "Bozza";
  let cls = "border-[#222] bg-[#111] text-[#9ca3af]";
  if (status === "paid" || hasPdf) {
    label = "Pagato";
    cls = "border-[var(--teal)]/60 bg-[#062120] text-[var(--teal)]";
  } else if (status === "report_ready") {
    label = "Report pronto";
    cls = "border-amber-700/50 bg-amber-900/20 text-amber-300";
  } else if (status === "active") {
    label = "In corso";
    cls = "border-[#222] bg-[#111] text-[#9ca3af]";
  }
  return (
    <span className={`rounded-full border px-2.5 py-1 text-[10px] uppercase tracking-wider ${cls}`}>
      {label}
    </span>
  );
}
