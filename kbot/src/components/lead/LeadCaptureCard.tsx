"use client";

import { useState } from "react";

export function LeadCaptureCard({ onSave }: { onSave: (email: string) => Promise<void> }) {
  const [email, setEmail] = useState("");
  const [busy, setBusy] = useState(false);

  async function handleSubmit() {
    if (!email.trim()) return;
    setBusy(true);
    try {
      await onSave(email);
      setEmail("");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="rounded-xl border border-[var(--line)] p-3">
      <p className="text-sm font-medium">Acquisizione lead</p>
      <div className="mt-2 flex gap-2">
        <input
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          placeholder="email@azienda.it"
          className="k2-focus w-full rounded-lg border border-[var(--line)] bg-transparent px-3 py-2 text-sm"
        />
        <button onClick={handleSubmit} disabled={busy} className="rounded-lg bg-[var(--teal)] px-3 py-2 text-xs font-semibold text-black">
          {busy ? "..." : "Salva"}
        </button>
      </div>
    </div>
  );
}
