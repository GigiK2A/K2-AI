"use client";

import { FormEvent, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useKbotAuth } from "@/app/providers";

type AuthFormProps = {
  mode: "login" | "register";
};

export function AuthForm({ mode }: AuthFormProps) {
  const router = useRouter();
  const { configured, signIn, signUp } = useKbotAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const isRegister = mode === "register";

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    setMessage("");

    if (!configured) {
      setError("Supabase non è configurato. Imposta NEXT_PUBLIC_SUPABASE_URL e NEXT_PUBLIC_SUPABASE_ANON_KEY.");
      return;
    }
    if (isRegister && password !== confirmPassword) {
      setError("Le password non coincidono.");
      return;
    }

    setLoading(true);
    try {
      if (isRegister) {
        await signUp(email, password);
        setMessage("Account creato. Se Supabase richiede conferma email, controlla la posta; altrimenti puoi entrare subito.");
      } else {
        await signIn(email, password);
        router.push("/app/");
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Accesso non riuscito.");
    } finally {
      setLoading(false);
    }
  }

  return (
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

        <label className="block">
          <span className="mb-1 block text-xs font-medium text-[#6b7280]">Password</span>
          <input
            type="password"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            autoComplete={isRegister ? "new-password" : "current-password"}
            required
            minLength={6}
            className="w-full rounded-lg border border-[#1f1f1f] bg-[#111] px-3 py-2.5 text-sm text-white outline-none focus:border-[#14b8a6]"
            placeholder="Minimo 6 caratteri"
          />
        </label>

        {isRegister && (
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
        )}

        {error && <p className="rounded-lg border border-red-900/40 bg-red-950/20 px-3 py-2 text-xs text-red-300">{error}</p>}
        {message && <p className="rounded-lg border border-teal-900/40 bg-teal-950/20 px-3 py-2 text-xs text-teal-200">{message}</p>}

        <button
          type="submit"
          disabled={loading}
          className="w-full rounded-lg bg-[#14b8a6] px-4 py-3 text-sm font-bold text-black transition hover:bg-[#2dd4bf] disabled:cursor-not-allowed disabled:opacity-60"
        >
          {loading ? "Attendi..." : isRegister ? "Crea account" : "Accedi"}
        </button>
      </div>

      <div className="mt-5 border-t border-[#1f1f1f] pt-4 text-center text-xs text-[#6b7280]">
        {isRegister ? (
          <p>
            Hai già un account?{" "}
            <Link href="/app/sign-in" className="font-semibold text-[#14b8a6]">
              Accedi
            </Link>
          </p>
        ) : (
          <p>
            Non hai un account?{" "}
            <Link href="/app/sign-up" className="font-semibold text-[#14b8a6]">
              Registrati
            </Link>
          </p>
        )}
      </div>
    </form>
  );
}
