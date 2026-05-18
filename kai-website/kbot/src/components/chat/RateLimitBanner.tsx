"use client";

import { useEffect, useState } from "react";
import { AlertTriangle } from "lucide-react";

export function RateLimitBanner({
  retryAt,
  onExpired,
}: {
  retryAt: number; // epoch ms
  onExpired: () => void;
}) {
  const [now, setNow] = useState(() => Date.now());

  useEffect(() => {
    const id = window.setInterval(() => setNow(Date.now()), 500);
    return () => window.clearInterval(id);
  }, []);

  const remaining = Math.max(0, Math.ceil((retryAt - now) / 1000));

  useEffect(() => {
    if (remaining <= 0) onExpired();
  }, [remaining, onExpired]);

  if (remaining <= 0) return null;

  return (
    <div
      role="alert"
      className="flex items-center gap-2 rounded-lg border border-red-500/40 bg-red-500/10 px-3 py-2 text-sm text-red-300"
    >
      <AlertTriangle size={14} />
      <span>
        Troppe richieste. Riprova fra <strong>{remaining}s</strong>.
      </span>
    </div>
  );
}
