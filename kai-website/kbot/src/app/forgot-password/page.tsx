"use client";

import { FormEvent, useState } from "react";
import Link from "next/link";
import { useKbotAuth } from "@/app/providers";

export default function ForgotPasswordPage() {
  const { configured, resetPassword } = useKbotAuth();
  const [email, setEmail] = useState("");
  const [loading, setLoading] = useState(false);
  const [sent, setSent] = useState(false);
  const [error, setError] = useState("");

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    if (!configured) {
      setError("Supabase non è configurato: recupero password non disponibile.");
      return;
    }
    setLoading(true);
    try {
      await resetPassword(email.trim());
      // Anti-enumeration: mostriamo conferma anche se l'email non esiste.
      setSent(true);
    } catch (err) {
      // Un errore reale (es. rate limit) va comunque comunicato senza rivelare l'esistenza dell'account.
      const msg = err instanceof Error ? err.message : "";
      if (/rate|too many|limit/i.test(msg)) {
        setError("Troppi tentativi. Riprova tra qualche minuto.");
      } else {
        setSent(true);
      }
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="flex min-h-screen items-center justify-center bg-[#050505] px-6 py-10 text-white">
      <div className="w-full max-w-sm">
        <div className="mb-6">
          <div className="mb-4 flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-[#14b8a6] font-black text-black">K</div>
            <span className="text-sm font-extrabold tracking-wide">K2-AI</span>
          </div>
          <h1 className="text-2xl font-extrabold">Recupera la password</h1>
          <p className="mt-2 text-sm text-[#6b7280]">
            Inserisci la tua email: se corrisponde a un account, ti inviamo un link per reimpostare la password.
          </p>
        </div>

        {sent ? (
          <div className="rounded-2xl border border-[#1f1f1f] bg-[#050505] p-6 shadow-2xl shadow-black/30">
            <p className="rounded-lg border border-teal-900/40 bg-teal-950/20 px-3 py-2 text-sm text-teal-200">
              Se l&apos;email è registrata, riceverai a breve un messaggio con il link per reimpostare la password.
              Controlla anche la cartella spam.
            </p>
            <div className="mt-5 border-t border-[#1f1f1f] pt-4 text-center text-xs text-[#6b7280]">
              <Link href="/sign-in" className="font-semibold text-[#14b8a6]">
                Torna al login
              </Link>
            </div>
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="rounded-2xl border border-[#1f1f1f] bg-[#050505] p-6 shadow-2xl shadow-black/30">
            <div className="space-y-4">
              <label className="block">
                <span className="mb-1 block text-xs font-medium text-[#6b7280]">Email</span>
                <input
                  type="email"
                  value={email}
                  onChange={(event) => setEmail(event.target.value)}
                  autoComplete="email"
                  required
                  className="w-full rounded-lg border border-[#1f1f1f] bg-[#111] px-3 py-2.5 text-sm text-white outline-none focus:border-[#14b8a6]"
                  placeholder="nome@azienda.it"
                />
              </label>

              {error && <p className="rounded-lg border border-red-900/40 bg-red-950/20 px-3 py-2 text-xs text-red-300">{error}</p>}

              <button
                type="submit"
                disabled={loading}
                className="w-full rounded-lg bg-[#14b8a6] px-4 py-3 text-sm font-bold text-black transition hover:bg-[#2dd4bf] disabled:cursor-not-allowed disabled:opacity-60"
              >
                {loading ? "Invio..." : "Invia link di recupero"}
              </button>
            </div>

            <div className="mt-5 border-t border-[#1f1f1f] pt-4 text-center text-xs text-[#6b7280]">
              <Link href="/sign-in" className="font-semibold text-[#14b8a6]">
                Torna al login
              </Link>
            </div>
          </form>
        )}
      </div>
    </main>
  );
}
