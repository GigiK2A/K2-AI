"use client";
import { useCallback, useEffect, useRef, useState } from "react";

const SOGLIA_FONDO = 64; // px dal fondo entro cui l'utente è «in fondo»

/**
 * Scroll della chat durante lo streaming.
 * Stato esplicito: `segue` (ref, letto a ogni cambio di altezza) e `lontano` (state, per il pulsante).
 *  - in fondo → segue la generazione, con assegnazione diretta di scrollTop (niente animazioni per token);
 *  - l'utente sale (rotella, tocco, tastiera, barra) → smette SUBITO di seguire e la posizione non si muove;
 *  - torna vicino al fondo, o preme «Vai in fondo» → riprende.
 * L'ancoraggio non usa scrollIntoView: il difetto precedente era uno scrollIntoView(smooth) a ogni token.
 */
export function useAutoScroll() {
  // ref a callback + state: il contenitore può comparire DOPO il primo render (la pagina mostra prima uno stato di caricamento)
  const [elContenitore, setElContenitore] = useState<HTMLElement | null>(null);
  const [elContenuto, setElContenuto] = useState<HTMLElement | null>(null);
  const contenitore = useCallback((el: HTMLElement | null) => setElContenitore(el), []);
  const contenuto = useCallback((el: HTMLElement | null) => setElContenuto(el), []);
  const elRef = useRef<HTMLElement | null>(null);
  elRef.current = elContenitore;
  const segue = useRef(true);
  const ultimoTop = useRef(0);
  const ultimoTocco = useRef<number | null>(null);
  const [lontano, setLontano] = useState(false);

  const alFondo = useCallback(() => {
    const el = elRef.current;
    if (!el) return;
    el.scrollTop = el.scrollHeight;
    ultimoTop.current = el.scrollTop;
  }, []);

  const riprendi = useCallback(() => {
    segue.current = true;
    setLontano(false);
    alFondo();
  }, [alFondo]);

  useEffect(() => {
    const el = elContenitore;
    if (!el) return;
    const sospendi = () => { segue.current = false; setLontano(true); };
    const onWheel = (e: WheelEvent) => { if (e.deltaY < 0) sospendi(); };
    const onTouchStart = (e: TouchEvent) => { ultimoTocco.current = e.touches[0]?.clientY ?? null; };
    const onTouchMove = (e: TouchEvent) => {
      const y = e.touches[0]?.clientY;
      if (y != null && ultimoTocco.current != null && y > ultimoTocco.current + 2) sospendi(); // dito verso il basso = contenuto verso l'alto
      if (y != null) ultimoTocco.current = y;
    };
    const onKey = (e: KeyboardEvent) => { if (["ArrowUp", "PageUp", "Home"].includes(e.key)) sospendi(); };
    const onScroll = () => {
      const dist = el.scrollHeight - el.scrollTop - el.clientHeight;
      if (el.scrollTop < ultimoTop.current - 1 && dist > SOGLIA_FONDO) sospendi(); // trascinamento della barra
      ultimoTop.current = el.scrollTop;
      if (dist <= SOGLIA_FONDO && !segue.current) { segue.current = true; setLontano(false); }
      else if (dist > SOGLIA_FONDO && !segue.current) setLontano(true);
    };
    el.addEventListener("wheel", onWheel, { passive: true });
    el.addEventListener("touchstart", onTouchStart, { passive: true });
    el.addEventListener("touchmove", onTouchMove, { passive: true });
    el.addEventListener("keydown", onKey);
    el.addEventListener("scroll", onScroll, { passive: true });
    return () => {
      el.removeEventListener("wheel", onWheel);
      el.removeEventListener("touchstart", onTouchStart);
      el.removeEventListener("touchmove", onTouchMove);
      el.removeEventListener("keydown", onKey);
      el.removeEventListener("scroll", onScroll);
    };
  }, [elContenitore]);

  // Cambi di altezza (token, tabelle, immagini): se si sta seguendo si resta in fondo, altrimenti non si tocca nulla.
  useEffect(() => {
    const c = elContenuto;
    if (!c || typeof ResizeObserver === "undefined") return;
    const ro = new ResizeObserver(() => { if (segue.current) alFondo(); });
    ro.observe(c);
    return () => ro.disconnect();
  }, [alFondo, elContenuto]);

  return { contenitore, contenuto, lontano, riprendi };
}
