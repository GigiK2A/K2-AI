"use client";

import { useEffect, useRef, useState } from "react";
import { ChevronLeft, ChevronRight, X, ZoomIn, ZoomOut } from "lucide-react";
import { getVistaDocumento, type VistaDocumento } from "@/lib/api";
import type { Citazione } from "@/lib/citazioni";

/**
 * Pannello laterale (desktop) / schermo intero (telefono) con il documento originale aperto al passaggio citato.
 * La chat resta dietro: chiudere il pannello non tocca lo stato della conversazione.
 * L'evidenziazione viene dai riquadri calcolati dal backend sulle parole reali della pagina (percentuali: reggono zoom e resize).
 */
export function VisualizzatoreDocumento({
  sessionId, getToken, citazione, elenco, onSeleziona, onChiudi,
}: {
  sessionId: string;
  getToken: () => Promise<string | null>;
  citazione: Citazione;
  elenco: Citazione[];
  onSeleziona: (c: Citazione) => void;
  onChiudi: () => void;
}) {
  const [vista, setVista] = useState<VistaDocumento | null>(null);
  const [errore, setErrore] = useState("");
  const [zoom, setZoom] = useState(100);
  const [pagina, setPagina] = useState(citazione.pag || 1);
  const evid = useRef<HTMLElement | null>(null);
  const tokenRef = useRef(getToken);   // getToken cambia a ogni render del chiamante: non deve rilanciare la richiesta
  tokenRef.current = getToken;

  // una nuova citazione riporta alla sua pagina
  useEffect(() => { setPagina(citazione.pag || 1); }, [citazione.doc, citazione.pag, citazione.quote]);

  useEffect(() => {
    let vivo = true;
    setErrore(""); setVista(null);
    (async () => {
      try {
        const token = await tokenRef.current();
        // il passaggio si evidenzia solo nella pagina da cui proviene
        const quote = pagina === (citazione.pag || 1) ? citazione.quote : "";
        const v = await getVistaDocumento(sessionId, citazione.doc, pagina, quote, token);
        if (vivo) setVista(v);
      } catch (e) {
        if (vivo) setErrore(e instanceof Error ? e.message : "Impossibile aprire il documento.");
      }
    })();
    return () => { vivo = false; };
  }, [sessionId, citazione, pagina]);

  // porta la zona evidenziata nell'area visibile appena la pagina è disegnata
  useEffect(() => { if (vista?.localizzato) evid.current?.scrollIntoView({ block: "center", behavior: "smooth" }); }, [vista, zoom]);

  const idx = elenco.findIndex((c) => c.doc === citazione.doc && c.pag === citazione.pag && c.quote === citazione.quote);

  return (
    <aside
      data-testid="visualizzatore"
      aria-label="Documento citato"
      className="fixed inset-0 z-40 flex flex-col border-[var(--line-strong)] bg-[var(--bg-1)] shadow-xl lg:inset-y-0 lg:left-auto lg:right-0 lg:w-[min(560px,46vw)] lg:border-l"
    >
      <header className="flex items-center gap-2 border-b border-[var(--line)] px-3 py-2">
        <div className="min-w-0 flex-1">
          <p className="truncate text-sm font-medium">{vista?.nome ?? "Documento"}</p>
          <p className="text-xs text-[var(--text-muted)]">
            {vista?.tipo === "pdf" ? `Pagina ${pagina}${vista.pagine ? ` di ${vista.pagine}` : ""}` : "Testo estratto"}
          </p>
        </div>
        {vista?.tipo === "pdf" && (
          <>
            <button type="button" aria-label="Pagina precedente" disabled={pagina <= 1} onClick={() => setPagina((p) => p - 1)} className="rounded p-1.5 hover:bg-[var(--bg-2)] disabled:opacity-30"><ChevronLeft size={16} /></button>
            <button type="button" aria-label="Pagina successiva" disabled={!vista.pagine || pagina >= vista.pagine} onClick={() => setPagina((p) => p + 1)} className="rounded p-1.5 hover:bg-[var(--bg-2)] disabled:opacity-30"><ChevronRight size={16} /></button>
            <button type="button" aria-label="Riduci" onClick={() => setZoom((z) => Math.max(60, z - 20))} className="rounded p-1.5 hover:bg-[var(--bg-2)]"><ZoomOut size={16} /></button>
            <button type="button" aria-label="Ingrandisci" onClick={() => setZoom((z) => Math.min(300, z + 20))} className="rounded p-1.5 hover:bg-[var(--bg-2)]"><ZoomIn size={16} /></button>
          </>
        )}
        <button type="button" aria-label="Torna alla conversazione" data-testid="chiudi-visualizzatore" onClick={onChiudi} className="inline-flex items-center gap-1 rounded-md border border-[var(--line-strong)] px-2 py-1 text-xs hover:border-[var(--teal)]"><X size={14} /> Chat</button>
      </header>

      {vista && (
        <p className="border-b border-[var(--line)] px-3 py-1.5 text-xs" role="status">
          {vista.localizzato ? <span className="text-[var(--teal)]">Passaggio citato evidenziato{citazione.quote ? `: «${citazione.quote}»` : ""}</span>
            : citazione.quote && pagina === (citazione.pag || 1)
              ? <span className="text-[var(--text-soft)]">Evidenziazione esatta non disponibile: ti mostro la pagina citata.</span>
              : <span className="text-[var(--text-muted)]">Pagina senza passaggio evidenziato.</span>}
        </p>
      )}

      <div className="scroll-premium flex-1 overflow-auto bg-[var(--bg-2)] p-3">
        {errore && <p className="text-sm text-red-700" role="alert">{errore}</p>}
        {!errore && !vista && <p className="text-sm text-[var(--text-muted)]">Apro il documento…</p>}
        {vista?.tipo === "pdf" && vista.immagine && (
          <div className="relative mx-auto bg-white shadow" style={{ width: `${zoom}%` }}>
            {/* eslint-disable-next-line @next/next/no-img-element -- pagina resa dal backend, dati base64 */}
            <img src={`data:image/png;base64,${vista.immagine}`} alt={`Pagina ${pagina}`} className="block w-full" />
            {vista.riquadri?.map((r, i) => (
              <span
                key={i}
                data-testid="evidenziazione"
                ref={i === 0 ? (el) => { evid.current = el; } : undefined}
                className="pointer-events-none absolute rounded-sm bg-yellow-300/50 ring-1 ring-yellow-500"
                style={{ left: `${r.x * 100}%`, top: `${r.y * 100}%`, width: `${r.w * 100}%`, height: `${r.h * 100}%` }}
              />
            ))}
          </div>
        )}
        {vista?.tipo === "testo" && vista.testo && (
          <pre className="whitespace-pre-wrap rounded bg-white p-3 text-[13px] leading-6 text-black">
            {vista.evidenzia ? (
              <>
                {vista.testo.slice(0, vista.evidenzia[0])}
                <mark ref={(el) => { evid.current = el; }} data-testid="evidenziazione" className="bg-yellow-300/70">{vista.testo.slice(vista.evidenzia[0], vista.evidenzia[1])}</mark>
                {vista.testo.slice(vista.evidenzia[1])}
              </>
            ) : vista.testo}
          </pre>
        )}
      </div>

      {elenco.length > 1 && (
        <footer className="flex items-center justify-between border-t border-[var(--line)] px-3 py-2 text-xs text-[var(--text-soft)]">
          <button type="button" disabled={idx <= 0} onClick={() => onSeleziona(elenco[idx - 1])} className="rounded px-2 py-1 hover:bg-[var(--bg-2)] disabled:opacity-30">← Citazione precedente</button>
          <span>{idx >= 0 ? idx + 1 : "–"} / {elenco.length}</span>
          <button type="button" disabled={idx < 0 || idx >= elenco.length - 1} onClick={() => onSeleziona(elenco[idx + 1])} className="rounded px-2 py-1 hover:bg-[var(--bg-2)] disabled:opacity-30">Citazione successiva →</button>
        </footer>
      )}
    </aside>
  );
}
