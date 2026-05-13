"use client";

import { useEffect, useState } from "react";
import { useAuth, UserButton } from "@clerk/nextjs";
import Link from "next/link";
import Image from "next/image";
import { ArrowLeft, BarChart3, CheckCircle2, Clock, Download, ExternalLink, FileText, Plus, XCircle } from "lucide-react";
import { fetchDashboard, DashboardData, DashboardReport } from "@/lib/api";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

function formatDate(iso: string) {
  if (!iso) return "—";
  return new Date(iso).toLocaleDateString("it-IT", { day: "2-digit", month: "short", year: "numeric", hour: "2-digit", minute: "2-digit" });
}

function ReportRow({ report, hasPaid, token }: { report: DashboardReport; hasPaid: boolean; token: string }) {
  return (
    <div className="flex items-center justify-between gap-4 rounded-xl border border-[#1f1f1f] bg-[#0a0a0a] px-4 py-3">
      <div className="flex min-w-0 flex-1 items-center gap-3">
        <FileText size={16} className="shrink-0 text-[#14b8a6]" />
        <div className="min-w-0">
          <p className="truncate text-sm font-medium text-white">{report.title}</p>
          <p className="text-xs text-[#6b7280]">{formatDate(report.created_at)}</p>
        </div>
      </div>
      <div className="flex shrink-0 items-center gap-2">
        {report.has_html && (
          <a
            href={`${API_BASE}${report.html_url}`}
            target="_blank"
            rel="noreferrer"
            className="flex items-center gap-1 rounded-lg border border-[#1f1f1f] px-2 py-1.5 text-xs text-[#d1d5db] hover:border-[#374151]"
          >
            <ExternalLink size={12} /> Apri
          </a>
        )}
        {hasPaid ? (
          <a
            href={`${API_BASE}${report.download_url}`}
            target="_blank"
            rel="noreferrer"
            onClick={(e) => {
              e.preventDefault();
              fetch(`${API_BASE}${report.download_url}`, {
                headers: { Authorization: `Bearer ${token}` },
              })
                .then((r) => r.blob())
                .then((blob) => {
                  const url = URL.createObjectURL(blob);
                  const a = document.createElement("a");
                  a.href = url;
                  a.download = report.filename;
                  a.click();
                  URL.revokeObjectURL(url);
                });
            }}
            className="flex items-center gap-1 rounded-lg bg-[#14b8a6] px-2 py-1.5 text-xs font-semibold text-black hover:bg-[#0d9488]"
          >
            <Download size={12} /> PDF
          </a>
        ) : (
          <span className="rounded-lg border border-[#1f1f1f] px-2 py-1.5 text-xs text-[#6b7280]">Acquista per scaricare</span>
        )}
      </div>
    </div>
  );
}

export default function DashboardPage() {
  const { getToken, isLoaded, isSignedIn } = useAuth();
  const [data, setData] = useState<DashboardData | null>(null);
  const [error, setError] = useState("");
  const [token, setToken] = useState("");

  useEffect(() => {
    if (!isLoaded || !isSignedIn) return;
    getToken().then(async (t) => {
      if (!t) return;
      setToken(t);
      try {
        const d = await fetchDashboard(t);
        setData(d);
      } catch (e) {
        setError(e instanceof Error ? e.message : "Errore caricamento dashboard");
      }
    });
  }, [isLoaded, isSignedIn, getToken]);

  if (!isLoaded) return null;

  if (!isSignedIn) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-[#050505]">
        <div className="text-center">
          <p className="mb-4 text-sm text-[#6b7280]">Accedi per vedere la dashboard</p>
          <Link href="/sign-in" className="rounded-xl bg-[#14b8a6] px-4 py-2 text-sm font-semibold text-black">
            Accedi
          </Link>
        </div>
      </div>
    );
  }

  const hasPaid = data?.account.has_paid ?? false;

  return (
    <div className="min-h-screen bg-[#050505] text-white">
      {/* Header */}
      <header className="sticky top-0 z-20 border-b border-[#111] bg-[rgba(5,5,5,0.9)] px-6 py-3 backdrop-blur">
        <div className="mx-auto flex max-w-5xl items-center justify-between">
          <div className="flex items-center gap-4">
            <Link href="/" className="flex items-center gap-2 text-[#6b7280] hover:text-white">
              <ArrowLeft size={16} />
              <span className="text-sm">Torna alla chat</span>
            </Link>
            <div className="h-4 w-px bg-[#1f1f1f]" />
            <div className="flex items-center gap-2">
              <Image src="/logo-k2ai.png" alt="K2-AI" width={24} height={24} className="rounded-lg" />
              <span className="text-sm font-semibold">Dashboard</span>
            </div>
          </div>
          <UserButton />
        </div>
      </header>

      <main className="mx-auto max-w-5xl px-6 py-8">
        {error && (
          <div className="mb-6 rounded-xl border border-red-900/40 bg-red-950/20 px-4 py-3 text-sm text-red-400">
            {error}
          </div>
        )}

        {/* Top cards */}
        <div className="mb-8 grid gap-4 sm:grid-cols-3">
          {/* Account */}
          <div className="rounded-xl border border-[#1f1f1f] bg-[#0a0a0a] p-4">
            <p className="mb-3 text-xs font-medium uppercase tracking-widest text-[#6b7280]">Account</p>
            <div className="flex items-center gap-2">
              {hasPaid ? (
                <CheckCircle2 size={18} className="text-[#14b8a6]" />
              ) : (
                <XCircle size={18} className="text-[#6b7280]" />
              )}
              <span className="text-sm font-semibold text-white">
                {hasPaid ? "Piano Premium attivo" : "Piano gratuito"}
              </span>
            </div>
            {!hasPaid && (
              <Link
                href="/"
                className="mt-3 block rounded-lg bg-[#14b8a6] px-3 py-2 text-center text-xs font-semibold text-black"
              >
                Attiva Premium
              </Link>
            )}
          </div>

          {/* Report count */}
          <div className="rounded-xl border border-[#1f1f1f] bg-[#0a0a0a] p-4">
            <p className="mb-3 text-xs font-medium uppercase tracking-widest text-[#6b7280]">Report generati</p>
            <p className="text-3xl font-bold text-white">{data?.stats.total_reports ?? "—"}</p>
          </div>

          {/* Last report */}
          <div className="rounded-xl border border-[#1f1f1f] bg-[#0a0a0a] p-4">
            <p className="mb-3 text-xs font-medium uppercase tracking-widest text-[#6b7280]">Ultimo report</p>
            <div className="flex items-center gap-2">
              <Clock size={14} className="text-[#6b7280]" />
              <span className="text-sm text-white">
                {data?.stats.last_report_at ? formatDate(data.stats.last_report_at) : "Nessuno ancora"}
              </span>
            </div>
          </div>
        </div>

        {/* Quick actions */}
        <div className="mb-8">
          <p className="mb-3 text-xs font-medium uppercase tracking-widest text-[#6b7280]">Azioni rapide</p>
          <div className="flex flex-wrap gap-3">
            <Link
              href="/"
              className="flex items-center gap-2 rounded-xl border border-[#14b8a6]/40 bg-[#14b8a6]/10 px-4 py-2.5 text-sm font-semibold text-[#14b8a6] hover:bg-[#14b8a6]/15"
            >
              <Plus size={15} /> Nuovo report
            </Link>
            {data?.reports[0] && (
              <a
                href={`${API_BASE}${data.reports[0].has_html ? data.reports[0].html_url : data.reports[0].url}`}
                target="_blank"
                rel="noreferrer"
                className="flex items-center gap-2 rounded-xl border border-[#1f1f1f] px-4 py-2.5 text-sm text-[#d1d5db] hover:border-[#374151]"
              >
                <ExternalLink size={15} /> Apri ultimo report
              </a>
            )}
          </div>
        </div>

        {/* Report history */}
        <div>
          <div className="mb-4 flex items-center justify-between">
            <p className="text-xs font-medium uppercase tracking-widest text-[#6b7280]">Storico report</p>
            <div className="flex items-center gap-1 text-xs text-[#6b7280]">
              <BarChart3 size={12} />
              {data?.stats.total_reports ?? 0} totali
            </div>
          </div>

          {!data && !error && (
            <div className="rounded-xl border border-[#1f1f1f] bg-[#0a0a0a] px-4 py-8 text-center text-sm text-[#6b7280]">
              Caricamento...
            </div>
          )}

          {data && data.reports.length === 0 && (
            <div className="rounded-xl border border-[#1f1f1f] bg-[#0a0a0a] px-4 py-10 text-center">
              <FileText size={32} className="mx-auto mb-3 text-[#374151]" />
              <p className="text-sm text-[#6b7280]">Nessun report ancora.</p>
              <Link
                href="/"
                className="mt-4 inline-flex items-center gap-2 rounded-xl bg-[#14b8a6] px-4 py-2 text-sm font-semibold text-black"
              >
                <Plus size={14} /> Genera il primo report
              </Link>
            </div>
          )}

          {data && data.reports.length > 0 && (
            <div className="flex flex-col gap-2">
              {data.reports.map((r) => (
                <ReportRow key={r.id} report={r} hasPaid={hasPaid} token={token} />
              ))}
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
