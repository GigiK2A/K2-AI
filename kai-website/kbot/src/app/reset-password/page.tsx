"use client";

import { FormEvent, useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { supabase } from "@/lib/supabase";
import { useKbotAuth } from "@/app/providers";

export default function ResetPasswordPage() {
  const router = useRouter();
  const { updatePassword } = useKbotAuth();
  const [checking, setChecking] = useState(true);
  const [ready, setReady] = useState(false);
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [done, setDone] = useState(false);

  /* Il link dell'email porta qui con i token nel fragment: detectSessionInUrl li
     consuma e apre una sessione di recupero (evento PASSWORD_RECOVERY). Aspettiamo
     quella sessione prima di mostrare il form. */
  useEffect(() => {
    let mounted = true;

    supabase.auth.getSession().then(({ data }) => {
      if (!mounted) return;
      if (data.session) {
        setReady(true);
        setChecking(false);
      }
    });

    const { data: listener } = supabase.auth.onAuthStateChange((event, nextSession) => {
      if (event === "PASSWORD_RECOVERY" || event === "SIGNED_IN" || nextSession) {
        setReady(true);
        setChecking(false);
      }
    });

    // Dopo un attimo, se non è arrivata nessuna sessione, il link è invalido/scaduto.
    const timer = window.setTimeout(() => {
      if (mounted) setChecking(false);
    }, 4000);

    return () => {
      mounted = false;
      window.clearTimeout(timer);
      listener.subscription.unsubscribe();
    };
  }, []);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    if (password !== confirmPassword) {
      setError("Le password non coincidono.");
      return;
    }
    if (password.length < 6) {
      setError("La password deve avere almeno 6 caratteri.");
      return;
    }
    setLoading(true);
    try {
      await updatePassword(password);
      setDone(true);
      window.setTimeout(() => router.push("/sign-in"), 2500);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Impossibile aggiornare la password.");
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
          <h1 className="text-2xl font-extrabold">Nuova password</h1>
          <p className="mt-2 text-sm text-[#6b7280]">Imposta una nuova password per il tuo account.</p>
        </div>

        <div className="rounded-2xl border border-[#1f1f1f] bg-[#050505] p-6 shadow-2xl shadow-black/30">
          {checking ? (
            <p className="text-sm text-[#6b7280]">Verifica del link in corso...</p>
          ) : done ? (
            <p className="rounded-lg border border-teal-900/40 bg-teal-950/20 px-3 py-2 text-sm text-teal-200">
              Password aggiornata. Ti reindirizzo al login...
            </p>
          ) : !ready ? (
            <div className="space-y-4">
              <p className="rounded-lg border border-red-900/40 bg-red-950/20 px-3 py-2 text-xs text-red-300">
                Link non valido o scaduto. Richiedi un nuovo link di recupero.
              </p>
              <Link
                href="/forgot-password"
                className="block w-full rounded-lg bg-[#14b8a6] px-4 py-3 text-center text-sm font-bold text-black transition hover:bg-[#2dd4bf]"
              >
                Richiedi un nuovo link
              </Link>
            </div>
          ) : (
            <form onSubmit={handleSubmit} className="space-y-4">
              <label className="block">
                <span className="mb-1 block text-xs font-medium text-[#6b7280]">Nuova password</span>
                <input
                  type="password"
                  value={password}
                  onChange={(event) => setPassword(event.target.value)}
                  autoComplete="new-password"
                  required
                  minLength={6}
                  className="w-full rounded-lg border border-[#1f1f1f] bg-[#111] px-3 py-2.5 text-sm text-white outline-none focus:border-[#14b8a6]"
                  placeholder="Minimo 6 caratteri"
                />
              </label>
              <label className="block">
                <span className="mb-1 block text-xs font-medium text-[#6b7280]">Conferma password</span>
                <input
                  type="password"
                  value={confirmPassword}
                  onChange={(event) => setConfirmPassword(event.target.value)}
                  autoComplete="new-password"
                  required
                  minLength={6}
                  className="w-full rounded-lg border border-[#1f1f1f] bg-[#111] px-3 py-2.5 text-sm text-white outline-none focus:border-[#14b8a6]"
                  placeholder="Ripeti la password"
                />
              </label>

              {error && <p className="rounded-lg border border-red-900/40 bg-red-950/20 px-3 py-2 text-xs text-red-300">{error}</p>}

              <button
                type="submit"
                disabled={loading}
                className="w-full rounded-lg bg-[#14b8a6] px-4 py-3 text-sm font-bold text-black transition hover:bg-[#2dd4bf] disabled:cursor-not-allowed disabled:opacity-60"
              >
                {loading ? "Aggiorno..." : "Aggiorna password"}
              </button>
            </form>
          )}
        </div>
      </div>
    </main>
  );
}
