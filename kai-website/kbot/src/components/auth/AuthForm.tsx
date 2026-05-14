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
  const [firstName, setFirstName] = useState("");
  const [lastName, setLastName] = useState("");
  const [email, setEmail] = useState("");
  const [workSector, setWorkSector] = useState("");
  const [companyName, setCompanyName] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [privacyAccepted, setPrivacyAccepted] = useState(false);
  const [termsAccepted, setTermsAccepted] = useState(false);
  const [marketingAccepted, setMarketingAccepted] = useState(false);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const isRegister = mode === "register";

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    setMessage("");

    if (!configured) {
      setError("Supabase non è configurato. Imposta NEXT_PUBLIC_SUPABASE_URL e NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY.");
      return;
    }
    if (isRegister && password !== confirmPassword) {
      setError("Le password non coincidono.");
      return;
    }
    if (isRegister && (!privacyAccepted || !termsAccepted)) {
      setError("Per registrarti devi accettare informativa privacy e termini di utilizzo.");
      return;
    }

    setLoading(true);
    try {
      if (isRegister) {
        await signUp(email, password, {
          firstName: firstName.trim(),
          lastName: lastName.trim(),
          workSector: workSector.trim(),
          companyName: companyName.trim() || undefined,
          privacyAccepted,
          termsAccepted,
          marketingAccepted,
        });
        setMessage("Account creato. Se Supabase richiede conferma email, controlla la posta; altrimenti puoi entrare subito.");
      } else {
        await signIn(email, password);
        router.push("/");
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
        {isRegister && (
          <div className="grid gap-3 sm:grid-cols-2">
            <label className="block">
              <span className="mb-1 block text-xs font-medium text-[#6b7280]">Nome</span>
              <input
                type="text"
                value={firstName}
                onChange={(event) => setFirstName(event.target.value)}
                autoComplete="given-name"
                required
                className="w-full rounded-lg border border-[#1f1f1f] bg-[#111] px-3 py-2.5 text-sm text-white outline-none focus:border-[#14b8a6]"
                placeholder="Nome"
              />
            </label>
            <label className="block">
              <span className="mb-1 block text-xs font-medium text-[#6b7280]">Cognome</span>
              <input
                type="text"
                value={lastName}
                onChange={(event) => setLastName(event.target.value)}
                autoComplete="family-name"
                required
                className="w-full rounded-lg border border-[#1f1f1f] bg-[#111] px-3 py-2.5 text-sm text-white outline-none focus:border-[#14b8a6]"
                placeholder="Cognome"
              />
            </label>
          </div>
        )}

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

        {isRegister && (
          <>
            <label className="block">
              <span className="mb-1 block text-xs font-medium text-[#6b7280]">Settore di lavoro</span>
              <input
                type="text"
                value={workSector}
                onChange={(event) => setWorkSector(event.target.value)}
                required
                className="w-full rounded-lg border border-[#1f1f1f] bg-[#111] px-3 py-2.5 text-sm text-white outline-none focus:border-[#14b8a6]"
                placeholder="Es. edilizia, hospitality, consulenza, real estate"
              />
            </label>

            <label className="block">
              <span className="mb-1 block text-xs font-medium text-[#6b7280]">Ragione sociale <span className="font-normal text-[#4b5563]">(opzionale)</span></span>
              <input
                type="text"
                value={companyName}
                onChange={(event) => setCompanyName(event.target.value)}
                autoComplete="organization"
                className="w-full rounded-lg border border-[#1f1f1f] bg-[#111] px-3 py-2.5 text-sm text-white outline-none focus:border-[#14b8a6]"
                placeholder="Nome azienda o studio"
              />
            </label>
          </>
        )}

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
          <>
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

            <div className="space-y-3 rounded-xl border border-[#1f1f1f] bg-[#090909] p-4 text-xs text-[#9ca3af]">
              <label className="flex gap-3">
                <input
                  type="checkbox"
                  checked={privacyAccepted}
                  onChange={(event) => setPrivacyAccepted(event.target.checked)}
                  required
                  className="mt-0.5 h-4 w-4 accent-[#14b8a6]"
                />
                <span>
                  Ho letto e accetto l&apos;informativa privacy e autorizzo il trattamento dei dati necessari alla gestione dell&apos;account e dei report.{" "}
                  <a href="/privacy.html" target="_blank" rel="noreferrer" className="font-semibold text-[#14b8a6]">
                    Privacy
                  </a>
                </span>
              </label>

              <label className="flex gap-3">
                <input
                  type="checkbox"
                  checked={termsAccepted}
                  onChange={(event) => setTermsAccepted(event.target.checked)}
                  required
                  className="mt-0.5 h-4 w-4 accent-[#14b8a6]"
                />
                <span>
                  Accetto termini e condizioni di utilizzo del servizio K2-AI.{" "}
                  <a href="/note-legali.html" target="_blank" rel="noreferrer" className="font-semibold text-[#14b8a6]">
                    Termini
                  </a>
                </span>
              </label>

              <label className="flex gap-3">
                <input
                  type="checkbox"
                  checked={marketingAccepted}
                  onChange={(event) => setMarketingAccepted(event.target.checked)}
                  className="mt-0.5 h-4 w-4 accent-[#14b8a6]"
                />
                <span>Acconsento a ricevere comunicazioni operative e aggiornamenti commerciali. Posso revocare il consenso in qualsiasi momento.</span>
              </label>
            </div>
          </>
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
            <Link href="/sign-in" className="font-semibold text-[#14b8a6]">
              Accedi
            </Link>
          </p>
        ) : (
          <p>
            Non hai un account?{" "}
            <Link href="/sign-up" className="font-semibold text-[#14b8a6]">
              Registrati
            </Link>
          </p>
        )}
      </div>
    </form>
  );
}
