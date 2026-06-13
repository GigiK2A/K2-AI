"use client";

import { useCallback, useEffect, useState } from "react";
import { useKbotAuth } from "@/app/providers";
import {
  getBilling,
  startSubscriptionCheckout,
  startCreditsCheckout,
  type BillingStatus,
} from "@/lib/api";

const PACCHETTI: { eur: 49 | 199 | 499; cr: number; consigliato?: boolean }[] = [
  { eur: 49, cr: 50 },
  { eur: 199, cr: 220, consigliato: true },
  { eur: 499, cr: 600 },
];

export default function BillingPanel() {
  const { isSignedIn, getToken } = useKbotAuth();
  const [data, setData] = useState<BillingStatus | null>(null);
  const [busy, setBusy] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      const token = await getToken();
      if (!token) return;
      setData(await getBilling(token));
    } catch (e) {
      setError(e instanceof Error ? e.message : "Errore");
    }
  }, [getToken]);

  useEffect(() => {
    // Fetch-on-signin: load() è async, lo setState avviene nel callback, non sincrono.
    // eslint-disable-next-line react-hooks/set-state-in-effect
    if (isSignedIn) void load();
  }, [isSignedIn, load]);

  const go = useCallback(
    async (action: () => Promise<string>, key: string) => {
      setBusy(key);
      setError(null);
      try {
        window.location.href = await action();
      } catch (e) {
        setError(e instanceof Error ? e.message : "Errore checkout");
        setBusy(null);
      }
    },
    [],
  );

  if (!isSignedIn) return null;

  const plan = data?.plan ?? "free";

  return (
    <section className="rounded-2xl border border-[#111] bg-[#0a0a0a] p-6 text-white">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-bold">Abbonamento &amp; crediti</h2>
        <span className="rounded-full border border-[#1d7d70] px-3 py-1 text-xs text-[#2a9d8f]">
          {data?.label ?? "Free"}
        </span>
      </div>

      <div className="mt-4 flex items-baseline gap-2">
        <span className="text-3xl font-bold tabular-nums">{data?.crediti ?? 0}</span>
        <span className="text-sm text-[#6b7280]">crediti disponibili</span>
        {data && data.crediti_mese > 0 && (
          <span className="ml-auto text-xs text-[#6b7280]">
            {data.crediti_mese}/mese · −{data.sconto_boost_pct}% sui Boost
          </span>
        )}
      </div>

      {error && <p className="mt-3 text-sm text-red-400">{error}</p>}

      {/* Piani */}
      {plan === "free" && (
        <div className="mt-5 grid gap-3 sm:grid-cols-2">
          <button
            disabled={busy !== null}
            onClick={() => go(() => getToken().then((t) => startSubscriptionCheckout("pro", t!)), "pro")}
            className="rounded-xl border border-[#1d7d70] bg-[#0d2420] p-4 text-left transition hover:bg-[#103029] disabled:opacity-50"
          >
            <div className="font-semibold">Pro · 49€/mese</div>
            <div className="text-xs text-[#6b7280]">50 crediti/mese · −10% sui Boost</div>
          </button>
          <button
            disabled={busy !== null}
            onClick={() => go(() => getToken().then((t) => startSubscriptionCheckout("business", t!)), "business")}
            className="rounded-xl border border-[#2a9d8f] bg-[#0d2420] p-4 text-left transition hover:bg-[#103029] disabled:opacity-50"
          >
            <div className="font-semibold">Studio · 149€/mese</div>
            <div className="text-xs text-[#6b7280]">200 crediti/mese · −20% · 3 utenti</div>
          </button>
        </div>
      )}

      {/* Pacchetti crediti */}
      <div className="mt-5">
        <p className="mb-2 text-xs uppercase tracking-wide text-[#6b7280]">Ricarica crediti</p>
        <div className="grid gap-3 sm:grid-cols-3">
          {PACCHETTI.map((p) => (
            <button
              key={p.eur}
              disabled={busy !== null}
              onClick={() => go(() => getToken().then((t) => startCreditsCheckout(p.eur, t!)), `cr${p.eur}`)}
              className={`relative rounded-xl border p-4 text-center transition hover:bg-[#111] disabled:opacity-50 ${
                p.consigliato ? "border-[#2a9d8f]" : "border-[#1f1f1f]"
              }`}
            >
              {p.consigliato && (
                <span className="absolute -top-2 left-1/2 -translate-x-1/2 rounded-full bg-[#2a9d8f] px-2 py-0.5 text-[10px] font-semibold text-black">
                  consigliato
                </span>
              )}
              <div className="text-xl font-bold tabular-nums">{p.cr}</div>
              <div className="text-xs text-[#6b7280]">crediti · {p.eur}€</div>
            </button>
          ))}
        </div>
      </div>

      <p className="mt-4 text-[11px] text-[#4b5563]">
        I crediti pagano i Check express (1 cr = 1€). I Boost si pagano a prezzo, con lo sconto del tuo piano.
      </p>
    </section>
  );
}
