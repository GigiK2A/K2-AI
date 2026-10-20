"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { AnimatePresence } from "framer-motion";
import { ChatLayoutHeader } from "@/components/layout/ChatLayout";
import { Sidebar } from "@/components/layout/Sidebar";
import { Composer } from "@/components/chat/Composer";
import { MessageBubble } from "@/components/chat/MessageBubble";
import { LoadingState } from "@/components/chat/LoadingState";
import { PannelloPratica, eBozza, estraiFonti, type SchedaPratica } from "@/components/pratica/PannelloPratica";
import { ReportGenerator } from "@/components/report/ReportGenerator";
import {
  streamMessage,
  uploadFiles,
  startCheckout,
  generatePdfStream,
  downloadDeliverableXlsx,
  downloadMessageExport,
  getSession,
  fetchUrl,
  listConversations,
  createRemoteConversation,
  updateRemoteConversation,
  deleteRemoteConversation,
  removeContextItem,
  fetchFollowUps,
  exchangeToken,
  RateLimitError,
  type UploadedFile,
  type AnalyzedUrl,
} from "@/lib/api";
import { RateLimitBanner } from "@/components/chat/RateLimitBanner";
import { track } from "@/lib/analytics";
import { ChatMessage, Conversation, Mode } from "@/types/chat";
import { uid } from "@/lib/utils";
import { AuthForm } from "@/components/auth/AuthForm";
import { useKbotAuth } from "@/app/providers";

const REPORT_SUGGESTIONS = [
  "Un cliente non mi paga una fattura",
  "Posso licenziare un dipendente?",
  "Devo aggiornare il DVR?",
  "Ho ricevuto una lettera dall'Agenzia delle Entrate",
];

const WELCOME_MESSAGE =
  "Ciao, sono K-BOT, il tuo pre-consulente per le questioni legali, fiscali, del lavoro e di bilancio. Raccontami il caso con i numeri che hai: importi, date, quanti dipendenti. Posso leggere i tuoi documenti, citare le norme in vigore e prepararti una bozza di lettera da far rivedere al tuo professionista.\n\nPrivacy: la conversazione viene elaborata da un modello di intelligenza artificiale. Dettagli su /privacy.html.";

function LoginFirstScreen() {
  return (
    <main className="flex min-h-screen items-center justify-center bg-[var(--bg-0)] px-6 py-10 text-[var(--text-main)]">
      <div className="grid w-full max-w-5xl overflow-hidden rounded-2xl border border-[var(--line)] bg-[var(--bg-1)] md:grid-cols-[0.95fr_1fr]">
        <section
          className="hidden min-h-[640px] flex-col justify-between p-10 md:flex"
          style={{ background: "var(--bg-2)" }}
        >
          <div className="flex items-center gap-3">
            {/* eslint-disable-next-line @next/next/no-img-element -- need explicit basePath, next/image overhead unnecessary */}
            <img
              src="/app/logo-k2ai.png"
              alt="K2-AI"
              width={120}
              height={48}
              className="h-12 w-auto"
            />
          </div>
          <div>
            <h1 className="text-3xl font-extrabold leading-tight">
              Accedi e apri la tua prima pratica
            </h1>
            <p className="mt-3 max-w-sm text-sm leading-6 text-[var(--text-soft)]">
              Le tue pratiche, i documenti e le bozze restano salvati sul tuo account, su computer e telefono.
            </p>
          </div>
          <p className="text-xs text-[var(--text-muted)]">
            K2-AI · pre-consulenza per le PMI italiane.
          </p>
        </section>

        <section className="flex min-h-[640px] flex-col items-center justify-center px-6 py-10">
          <div className="mb-8 text-center md:hidden">
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img
              src="/app/logo-k2ai.png"
              alt="K2-AI"
              width={140}
              height={56}
              className="mx-auto mb-3 h-14 w-auto"
            />
            <p className="text-lg font-bold">K-BOT</p>
          </div>
          <div className="w-full max-w-sm">
            <div className="mb-6">
              <h2 className="text-xl font-bold">Accedi al tuo account</h2>
              <p className="mt-1 text-sm text-[var(--text-muted)]">
                Dopo l&apos;accesso si apre la tua pratica.
              </p>
            </div>
            <AuthForm mode="login" />
          </div>
        </section>
      </div>
    </main>
  );
}

export default function HomePage() {
  const { loading: authLoading, getToken, isSignedIn, hasPaid, ensureSession, resetSession, refreshSession, kbotSession } =
    useKbotAuth();

  const [mode] = useState<Mode>("report");
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [scheda, setScheda] = useState<SchedaPratica>("bozza");
  const [pannelloAperto, setPannelloAperto] = useState(false);
  const [fatti, setFatti] = useState<Record<string, string>>({});
  const [loading, setLoading] = useState(false);
  const [composer, setComposer] = useState("");
  const [usedSkills, setUsedSkills] = useState<string[]>([]);
  // Boost suggerito dal routing chat→catalogo (selettore): popolato da res.session
  // a fine conversazione, fa comparire il DeliverablePanel generato via 8e.
  const [suggestedBoost, setSuggestedBoost] = useState<{ id: string; label?: string } | null>(null);
  const [error, setError] = useState("");
  const [pendingFiles, setPendingFiles] = useState<UploadedFile[]>([]);
  const [uploadingFiles, setUploadingFiles] = useState<
    { name: string; size: number; type: string }[]
  >([]);
  const [contextFilesByConversation, setContextFilesByConversation] = useState<
    Record<string, UploadedFile[]>
  >({});
  const [fetchingUrl, setFetchingUrl] = useState(false);
  const [analyzedUrls, setAnalyzedUrls] = useState<AnalyzedUrl[]>([]);
  const [forcedSkills] = useState<string[]>([]);
  const [rateLimitUntil, setRateLimitUntil] = useState<number | null>(null);
  const [pdfProgress, setPdfProgress] = useState<{ stage: string; progress: number } | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Track kbot_open once the chat surface mounts for an authenticated user.
  useEffect(() => {
    if (!authLoading && isSignedIn) {
      track("kbot_open", { surface: "kbot_app" });
    }
  }, [authLoading, isSignedIn]);

  // State definitions must come BEFORE the bootstrap effect below so that
  // the setters aren't referenced in a TDZ context (react-hooks lint rule).
  const [conversations, setConversations] = useState<Conversation[]>([
    {
      id: uid("conv"),
      title: "Nuova pratica",
      mode: "report",
      messages: [
        { id: uid("msg"), role: "assistant", content: WELCOME_MESSAGE, ts: 0 },
      ],
    },
  ]);
  const [activeId, setActiveId] = useState(conversations[0].id);

  // Bootstrap: load remote conversations on first authed render.
  // Anon: keep the in-memory single welcome conv.
  const [bootstrapped, setBootstrapped] = useState(false);
  useEffect(() => {
    if (bootstrapped || authLoading || !isSignedIn) return;
    let cancelled = false;
    (async () => {
      try {
        const token = await getToken();
        if (!token) return;
        const remote = await listConversations(token);
        if (cancelled || remote.length === 0) return;
        // La chat in corso (sessione viva o salvata) può non avere ancora una conversazione remota: la prima chat
        // non ne crea una. Se la si sostituisse con l'elenco remoto, tornando dalla dashboard sparirebbe.
        let sessioneInCorso: string | null = kbotSession?.id ?? null;
        if (!sessioneInCorso) {
          try { sessioneInCorso = window.localStorage.getItem("kbot.session_id"); } catch { sessioneInCorso = null; }
        }
        const tenereLocale = !!sessioneInCorso && !remote.some((r) => r.kbotSessionId === sessioneInCorso);
        const localeId = (conversations.find((c) => !c.remoteId) ?? conversations[0]).id;
        const mapped: Conversation[] = remote.map((r) => ({
          id: r.id,
          remoteId: r.id,
          title: r.title || "Nuova pratica",
          mode: r.mode,
          kbotSessionId: r.kbotSessionId,
          messages: [{ id: uid("msg"), role: "assistant", content: WELCOME_MESSAGE, ts: 0 }],
        }));
        if (tenereLocale) {
          setConversations((prev) => {
            const locale = prev.find((c) => c.id === localeId) ?? prev[0];
            return [locale, ...mapped.filter((m) => m.id !== locale.id)];
          });
          setActiveId(localeId);
        } else {
          setConversations(mapped);
          setActiveId(mapped[0].id);
        }
      } catch {
        /* anon o errore di rete: lasciamo la conv locale */
      } finally {
        if (!cancelled) setBootstrapped(true);
      }
    })();
    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [authLoading, isSignedIn]);

  /* Restore al MOUNT (bug "chat persa al refresh"): se localStorage ha una sessione
     salvata, la ripristiniamo SUBITO — senza aspettare il primo messaggio — così la
     cronologia (persistita dal backend su Supabase) riappare dopo il refresh. */
  useEffect(() => {
    // Ritorno da un'altra pagina (dashboard): la sessione c'è già nel provider ma può essere «vecchia» → la si rilegge,
    // così il re-idrata sotto riporta i messaggi. Al primo caricamento (nessuna sessione) vale il ramo localStorage.
    if (!authLoading && kbotSession?.id) { void refreshSession(); return; }
    if (authLoading || kbotSession?.id) return;
    let stored: string | null = null;
    try { stored = window.localStorage.getItem("kbot.session_id"); } catch { stored = null; }
    if (stored) void ensureSession({ mode: "report" });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [authLoading]);

  /* Re-idrata i MESSAGGI nella UI quando la sessione ripristinata li porta: se la
     conversazione attiva è ancora stub (solo welcome), la cronologia backend viene
     mappata dentro. Copre anonimi (nessun lazy-load esisteva) e loggati al refresh
     (il lazy-load scattava solo al click in sidebar, non sulla conv attiva). */
  const kbotSessionMsgCount = kbotSession?.messages?.length ?? 0;
  const kbotSessionId = kbotSession?.id ?? null;
  useEffect(() => {
    const backendMsgs = kbotSession?.messages || [];
    if (!kbotSession?.id || backendMsgs.length === 0) return;
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setConversations((prev) =>
      prev.map((c) => {
        if (c.id !== activeId) return c;
        if ((c.messages?.length ?? 0) > 1) return c;              // conversazione già viva
        if (c.kbotSessionId && c.kbotSessionId !== kbotSession.id) return c;
        const mapped: ChatMessage[] = [
          { id: uid("msg"), role: "assistant", content: WELCOME_MESSAGE, ts: 0 },
          ...backendMsgs
            .filter((m) => typeof m.content === "string" && m.content)
            .map((m) => ({
              id: uid("msg"),
              role: (m.role === "user" ? "user" : "assistant") as "user" | "assistant",
              content: m.content as string,
              ts: Date.now(),
            })),
        ];
        return { ...c, kbotSessionId: kbotSession.id, messages: mapped };
      }),
    );
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [kbotSessionId, kbotSessionMsgCount]);

  /* Le skill usate stanno nella sessione del backend (extractedData.used_skills): dopo un refresh o il ritorno dalla
     dashboard lo stato locale è vuoto e il pannello diceva «in attesa del primo turno» a conversazione avviata. */
  useEffect(() => {
    const us = (kbotSession?.extractedData as { used_skills?: string[] } | undefined)?.used_skills;
    // eslint-disable-next-line react-hooks/set-state-in-effect
    if (Array.isArray(us) && us.length > 0 && usedSkills.length === 0) setUsedSkills(us);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [kbotSession?.id, kbotSession?.extractedData]);

  /* I fatti del cliente stanno nella sessione del backend: dopo refresh o ritorno dalla dashboard si ripristinano. */
  useEffect(() => {
    const sc = kbotSession?.schedaCliente;
    // eslint-disable-next-line react-hooks/set-state-in-effect
    if (sc) setFatti(sc);
  }, [kbotSession?.id, kbotSession?.schedaCliente]);

  /* Cross-bot bridge: when arriving from suite-ai widget with ?continue=<id>,
     adopt that session id instead of creating a new one. Also picks up the
     pillar tag (scenario C) from ?tag= or sessionStorage["kbot.tag_pillar"]
     set by the site (js/kbot-tag.js) → la sessione nasce col contesto del
     pillar e il backend calcola il boost suggerito. Stripped after read. */
  useEffect(() => {
    if (typeof window === "undefined") return;
    const url = new URL(window.location.href);
    const carry = url.searchParams.get("continue") || url.searchParams.get("kbot_session");
    let tag = url.searchParams.get("tag");
    if (!tag) {
      try { tag = sessionStorage.getItem("kbot.tag_pillar"); } catch { tag = null; }
    }
    if (!carry && !tag) return;
    void ensureSession({ mode: "report", adopt: carry ?? undefined, tagPillar: tag ?? undefined });
    url.searchParams.delete("continue");
    url.searchParams.delete("kbot_session");
    url.searchParams.delete("tag");
    try { sessionStorage.removeItem("kbot.tag_pillar"); } catch { /* ignore */ }
    window.history.replaceState({}, "", url.toString());
  }, [ensureSession]);

  /* Rientro post-redirect Stripe: ?kbot_paid=1&t=<success_token>. Il frontend ha
     il token ma non il session_id (non viaggia nell'URL, H-7). Scambia il token →
     session_id, adotta la sessione (ora paid) e segna il resume: ReportGenerator
     riprende la generazione da solo. Senza questo, il cliente paga e vede la UI
     vecchia (il ponte pagamento→report era rotto). */
  useEffect(() => {
    if (typeof window === "undefined") return;
    const url = new URL(window.location.href);
    if (url.searchParams.get("kbot_paid") !== "1") return;
    const token = url.searchParams.get("t");
    // pulisci subito i parametri (evita ri-trigger su refresh/replaceState)
    url.searchParams.delete("kbot_paid");
    url.searchParams.delete("t");
    url.searchParams.delete("cs");
    window.history.replaceState({}, "", url.toString());
    if (!token) return;
    void (async () => {
      try {
        const r = await exchangeToken(token);
        if (!r?.session_id) return;
        await ensureSession({ mode: "report", adopt: r.session_id });
        // segnala a ReportGenerator di riprendere la generazione per questa sessione
        try { sessionStorage.setItem("kbot.pay_resume", r.session_id); } catch { /* ignore */ }
      } catch { /* il polling/stato a valle gestisce il resto */ }
    })();
  }, [ensureSession]);

  const activeConversation = useMemo(
    () => conversations.find((c) => c.id === activeId) ?? conversations[0],
    [conversations, activeId],
  );

  // Il bottone "Genera il report" deve riflettere la prontezza CORRENTE, non il boost
  // persistito sulla sessione (che restava settato → su una chat continuata il bottone
  // compariva subito dopo un semplice "ciao"). Lo mostriamo se l'ULTIMO messaggio del
  // bot è in stato pronto (nextAction=show_summary → reportReady); fallback al boost
  // persistito SOLO quando non c'è ancora un segnale di prontezza (es. al reload).
  const reportReady = useMemo(() => {
    const lastAssistant = [...activeConversation.messages].reverse().find((m) => m.role === "assistant");
    return lastAssistant?.reportReady ?? Boolean(kbotSession?.boostSuggerito);
  }, [activeConversation.messages, kbotSession?.boostSuggerito]);

  // Auto-scroll to bottom on new messages / streaming deltas / loading state.
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [activeConversation.messages.length, activeConversation.messages.at(-1)?.content, loading]);

  /* Per-conversation backend session: each sidebar conv must talk to its OWN
     kbot_sessions row, otherwise switching/creating conversations leaks
     uploaded_files + analyzed_urls across topics (es. un bilancio + un sito web). */
  useEffect(() => {
    // Il boost suggerito appartiene alla CONVERSAZIONE: senza questo reset il
    // pannello della chat precedente "rimaneva appiccicato" e compariva subito
    // (col boost sbagliato) al 1° messaggio della chat nuova. Reset legittimo al
    // cambio di conversazione (dipendenza activeConversation.id).
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setSuggestedBoost(null);
    const convSid = activeConversation.kbotSessionId ?? null;
    const liveSid = kbotSession?.id ?? null;
    if (convSid && convSid !== liveSid) {
      // Switch backend session to the one bound to this conversation.
      resetSession();
      void ensureSession({ mode: activeConversation.mode, adopt: convSid });
    } else if (!convSid && liveSid) {
      // Sessione viva che nessuna conversazione possiede: è il caso del RITORNO dalla dashboard (la pagina si
      // rimonta con una conversazione nuova, ma il provider ha ancora la sessione). Prima la si azzerava sempre:
      // la chat spariva (segnalato il 20/10/2026). Ora resta: l'effetto «Bind» qui sotto la lega a questa
      // conversazione e la cronologia si re-idrata. Si scarta solo se appartiene a UN'ALTRA conversazione
      // (altrimenti il messaggio successivo finirebbe nella chat sbagliata).
      const posseduta = conversations.some((c) => c.id !== activeConversation.id && c.kbotSessionId === liveSid);
      if (posseduta) resetSession();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activeConversation.id]);

  /* Bind backend session id back to the active conversation once known. */
  useEffect(() => {
    if (!kbotSession?.id) return;
    let remoteIdToSync: string | null | undefined;
    // Syncing local state with an external system (backend session id from
    // the kbot API), which is exactly the documented "OK" case for setState
    // inside an effect.
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setConversations((prev) =>
      prev.map((c) => {
        if (c.id !== activeConversation.id || c.kbotSessionId === kbotSession.id) return c;
        remoteIdToSync = c.remoteId;
        return { ...c, kbotSessionId: kbotSession.id };
      }),
    );
    if (remoteIdToSync && isSignedIn) {
      void (async () => {
        try {
          const token = await getToken();
          if (token)
            await updateRemoteConversation(token, remoteIdToSync!, {
              kbotSessionId: kbotSession.id,
            });
        } catch {
          /* ignore */
        }
      })();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [kbotSession?.id, activeConversation.id]);

  function updateMessages(next: ChatMessage[]) {
    setConversations((prev) =>
      prev.map((c) => (c.id === activeConversation.id ? { ...c, messages: next } : c)),
    );
  }

  /** Imposta titolo conv se ancora generico ("Nuova pratica" / "Nuova pratica"). */
  function maybeSetTitle(label: string) {
    const clean = label.trim().replace(/\s+/g, " ").slice(0, 48);
    if (!clean) return;
    let updatedRemoteId: string | null | undefined;
    setConversations((prev) =>
      prev.map((c) => {
        if (c.id !== activeConversation.id) return c;
        const isGeneric = !c.title || /^Nuova (chat|conversazione|pratica)$/i.test(c.title);
        if (!isGeneric) return c;
        updatedRemoteId = c.remoteId;
        return { ...c, title: clean };
      }),
    );
    if (updatedRemoteId && isSignedIn) {
      void (async () => {
        try {
          const token = await getToken();
          if (token) await updateRemoteConversation(token, updatedRemoteId!, { title: clean });
        } catch {
          /* ignore */
        }
      })();
    }
  }

  function handleRenameConversation(convId: string, nextTitle: string) {
    const clean = nextTitle.trim().slice(0, 80);
    if (!clean) return;
    setConversations((prev) =>
      prev.map((c) => (c.id === convId ? { ...c, title: clean } : c)),
    );
  }


  async function handleRemoveContext({
    type,
    idOrName,
  }: {
    type: "file" | "url";
    idOrName: string;
  }) {
    const sessionId = activeConversation.kbotSessionId ?? kbotSession?.id ?? null;
    // Optimistic UI update first.
    if (type === "file") {
      setPendingFiles((prev) =>
        prev.filter((f) => f.path !== idOrName && f.name !== idOrName),
      );
      setContextFilesByConversation((prev) => {
        const cur = prev[activeConversation.id] ?? [];
        return {
          ...prev,
          [activeConversation.id]: cur.filter(
            (f) => f.path !== idOrName && f.name !== idOrName,
          ),
        };
      });
    } else {
      setAnalyzedUrls((prev) => prev.filter((u) => u.url !== idOrName));
    }
    if (!sessionId) return;
    try {
      const token = await getToken();
      await removeContextItem(sessionId, type, idOrName, token);
    } catch (err) {
      // Non-fatal: backend cleanup failed but local state is already updated.
      setError(err instanceof Error ? err.message : "Errore rimozione contesto");
    }
  }

  function handleDeleteConversation(convId: string) {
    const target = conversations.find((c) => c.id === convId);
    setConversations((prev) => {
      const filtered = prev.filter((c) => c.id !== convId);
      // If we deleted the active one, switch to the first remaining (or create empty)
      if (convId === activeId) {
        if (filtered.length > 0) {
          setActiveId(filtered[0].id);
        } else {
          const fresh: Conversation = {
            id: uid("conv"),
            title: "Nuova pratica",
            mode,
            messages: [{ id: uid("msg"), role: "assistant", content: WELCOME_MESSAGE, ts: 0 }],
          };
          setActiveId(fresh.id);
          return [fresh];
        }
      }
      return filtered;
    });
    // Drop the kbot session id from localStorage so the next message starts fresh
    resetSession();
    // Persist soft-delete server-side (best-effort, anon fa nulla).
    if (target?.remoteId && isSignedIn) {
      void (async () => {
        try {
          const token = await getToken();
          if (token) await deleteRemoteConversation(token, target.remoteId!);
        } catch {
          /* ignore */
        }
      })();
    }
  }

  function handleNewConversation() {
    resetSession(); // start a fresh kbot_sessions row on the next message
    const localId = uid("conv");
    const newConv: Conversation = {
      id: localId,
      title: "Nuova pratica",
      mode,
      messages: [
        { id: uid("msg"), role: "assistant", content: WELCOME_MESSAGE, ts: 0 },
      ],
      kbotSessionId: null, // backend session creato on demand alla 1ª azione
      remoteId: null,
    };
    setConversations((prev) => [newConv, ...prev]);
    setActiveId(newConv.id);
    setComposer("");
    setUsedSkills([]);
    setPendingFiles([]);
    setAnalyzedUrls([]); // drop URL analizzati della conv precedente

    // Persist server-side for authed user (anon = noop).
    if (isSignedIn) {
      void (async () => {
        try {
          const token = await getToken();
          if (!token) return;
          const remote = await createRemoteConversation(token, {
            title: "Nuova pratica",
            mode,
          });
          setConversations((prev) =>
            prev.map((c) =>
              c.id === localId ? { ...c, remoteId: remote.id, id: remote.id } : c,
            ),
          );
          setActiveId((prev) => (prev === localId ? remote.id : prev));
        } catch {
          /* ignore */
        }
      })();
    }
  }

  const handleFilePick = useCallback(
    async (files: File[]) => {
      setError("");
      // Show uploading placeholders immediately (animated chip in Composer).
      const placeholders = files.map((f) => ({
        name: f.name,
        size: f.size,
        type: f.type,
      }));
      setUploadingFiles((prev) => [...prev, ...placeholders]);
      try {
        const session = await ensureSession({ mode });
        const token = await getToken();
        const uploaded = await uploadFiles(session.id, files, token);
        setPendingFiles((prev) => [...prev, ...uploaded]);
        setContextFilesByConversation((prev) => ({
          ...prev,
          [activeConversation.id]: [...(prev[activeConversation.id] ?? []), ...uploaded],
        }));
        // Auto-title: nome del 1° file caricato (senza estensione).
        if (uploaded[0]) {
          const base = uploaded[0].name.replace(/\.[^.]+$/, "");
          maybeSetTitle(base);
        }
      } catch (e) {
        setError(e instanceof Error ? e.message : "Errore upload file");
      } finally {
        // Drop the placeholders we added (match by name+size).
        setUploadingFiles((prev) =>
          prev.filter(
            (p) =>
              !placeholders.some((q) => q.name === p.name && q.size === p.size),
          ),
        );
      }
    },
    [activeConversation.id, ensureSession, getToken, mode],
  );

  const handleFetchUrl = useCallback(
    async (url: string) => {
      if (fetchingUrl) return;
      setFetchingUrl(true);
      try {
        const session = await ensureSession({ mode });
        const token = await getToken();
        const result = await fetchUrl(session.id, url, token ?? null);
        setAnalyzedUrls((prev) => {
          const exists = prev.some((u) => u.url === url);
          return exists ? prev : [...prev, result];
        });
        // Auto-title: hostname + path corto.
        try {
          const u = new URL(url);
          maybeSetTitle(u.hostname.replace(/^www\./, "") + (u.pathname !== "/" ? u.pathname : ""));
        } catch {
          /* ignore */
        }
        // Niente bubble-ack qui: l'URL compare già nel chip "Contesto attivo" del Composer.
        // Aggiungerne una si intrometteva nel flusso (messaggio K2-AI fuori posto, prima
        // della risposta vera) → era il "primo messaggio col link disordinato".
      } catch (err: unknown) {
        const errMsg: ChatMessage = {
          id: uid("msg"),
          role: "assistant",
          content: `Non riesco ad analizzare l'URL: ${err instanceof Error ? err.message : "errore sconosciuto"}.`,
          ts: Date.now(),
        };
        // Updater funzionale: appende ai messaggi CORRENTI, non a uno snapshot stantio.
        setConversations((prev) =>
          prev.map((c) => (c.id === activeConversation.id ? { ...c, messages: [...c.messages, errMsg] } : c)),
        );
      } finally {
        setFetchingUrl(false);
      }
    },
    [activeConversation.messages, ensureSession, fetchingUrl, getToken, mode],
  );

  async function handleSubmit(overrideText?: string) {
    const promptInput = (overrideText ?? composer).trim();
    if (!promptInput || loading) return;
    if (rateLimitUntil && rateLimitUntil > Date.now()) return;

    setError("");
    setLoading(true);
    const userMessage: ChatMessage = {
      id: uid("msg"),
      role: "user",
      content: promptInput,
      ts: Date.now(),
      attachments: pendingFiles,
    };
    const stubMessage: ChatMessage = {
      id: uid("msg"),
      role: "assistant",
      content: "",
      ts: Date.now(),
    };
    const currentMessages = [...activeConversation.messages, userMessage, stubMessage];
    updateMessages(currentMessages);
    // Auto-title: prime parole del 1° messaggio utente (se conv ancora generica).
    maybeSetTitle(promptInput);

    const prompt = promptInput;
    track("kbot_message_sent", { length: prompt.length, mode });
    setComposer("");
    setPendingFiles([]);

    try {
      const session = await ensureSession({ mode });
      const token = await getToken();
      // Live-update the stub message as deltas stream in.
      const patchStub = (patch: Partial<ChatMessage>) => {
        setConversations((prev) =>
          prev.map((c) =>
            c.id === activeConversation.id
              ? {
                  ...c,
                  messages: c.messages.map((m) =>
                    m.id === stubMessage.id ? { ...m, ...patch } : m,
                  ),
                }
              : c,
          ),
        );
      };

      let streamed = "";
      let finalMessage = "";
      await streamMessage(session.id, prompt, {
        authToken: token,
        forcedSkills: forcedSkills.length ? forcedSkills : undefined,
        onDelta: (chunk) => {
          streamed += chunk;
          patchStub({ content: streamed, sessionId: session.id });
        },
        onDone: (res) => {
          finalMessage = res.message;
          const skills =
            (res.session?.extractedData as { used_skills?: string[] } | undefined)
              ?.used_skills ?? [];
          setUsedSkills(skills);
          const sc = (res.session as { schedaCliente?: Record<string, string> } | undefined)?.schedaCliente;
          if (sc) setFatti(sc);
          // Selettore di catalogo: il backend ha pre-scelto il Boost 8e → mostra il pannello.
          const sess = res.session as
            | { boostSuggerito?: string; boostSuggeritoLabel?: string }
            | undefined;
          if (sess?.boostSuggerito) {
            setSuggestedBoost({ id: sess.boostSuggerito, label: sess.boostSuggeritoLabel });
          }
          patchStub({
            content: res.message,
            reportReady: res.nextAction === "show_summary",
            sessionId: session.id,
          });
        },
      });

      // La scheda dei fatti si aggiorna a fine turno: rileggila (non blocca, non tocca i messaggi).
      void refreshSession().catch(() => undefined);

      // Long-form report → fetch follow-up suggestions (non-blocking).
      if (finalMessage && finalMessage.length > 1500) {
        void (async () => {
          try {
            const ups = await fetchFollowUps(session.id, token);
            if (ups.length) {
              patchStub({ followUps: ups });
            }
          } catch {
            /* silent */
          }
        })();
      }
    } catch (e) {
      if (e instanceof RateLimitError) {
        setRateLimitUntil(Date.now() + e.retryAfter * 1000);
        setError("");
      } else {
        setError(e instanceof Error ? e.message : "Errore imprevisto");
      }
      updateMessages(activeConversation.messages);
    } finally {
      setLoading(false);
    }
  }

  function handleFollowUpClick(text: string) {
    void handleSubmit(text);
  }

  async function startCheckoutFromUI() {
    const session = await ensureSession({ mode });
    track("kbot_report_requested", { mode });
    const token = await getToken();
    if (!token) return;
    const url = await startCheckout(session.id, token);
    window.location.href = url;
  }

  /** Fase free: genera il PDF in streaming SSE, progress real-time + url al messaggio. */
  async function generateReportPdfFromUI(messageId: string) {
    const session = await ensureSession({ mode });
    track("kbot_pdf_generation_requested", { mode });
    const token = await getToken();
    setLoading(true);
    setError("");
    setPdfProgress({ stage: "Avvio generazione...", progress: 2 });
    try {
      const { pdfUrl } = await generatePdfStream(session.id, {
        authToken: token,
        testMode: true,
        onProgress: (e) => setPdfProgress(e),
      });
      setConversations((prev) =>
        prev.map((c) =>
          c.id === activeConversation.id
            ? {
                ...c,
                messages: c.messages.map((m) =>
                  m.id === messageId ? { ...m, reportPdfUrl: pdfUrl } : m,
                ),
              }
            : c,
        ),
      );
    } catch (e) {
      setError(e instanceof Error ? e.message : "Errore generazione PDF");
    } finally {
      setLoading(false);
      setPdfProgress(null);
    }
  }

  // Contenuti della pratica (pannello a destra): bozza, documenti, fonti. I fatti arrivano dal backend.
  const bozzaIdx = (() => {
    for (let i = activeConversation.messages.length - 1; i >= 0; i--) {
      const m = activeConversation.messages[i];
      if (m.role === "assistant" && m.ts > 0 && eBozza(m.content)) return i;
    }
    return -1;
  })();
  const bozza = bozzaIdx >= 0 ? activeConversation.messages[bozzaIdx].content.replace(/\n+Fonti:[^\n]*$/i, "").trim() : null;
  const fonti = estraiFonti(activeConversation.messages.filter((m) => m.role === "assistant").map((m) => m.content));
  const documentiPratica = (() => {
    const viste = new Map<string, UploadedFile>();
    for (const f of contextFilesByConversation[activeConversation.id] ?? []) viste.set(f.path, f);
    for (const m of activeConversation.messages) for (const f of m.attachments ?? []) viste.set(f.path, f);
    return [...viste.values()];
  })();

  async function scaricaBozzaWord() {
    const sid = activeConversation.kbotSessionId ?? kbotSession?.id;
    if (!sid || bozzaIdx < 1) throw new Error("La bozza non è ancora salvata: riprova tra un momento.");
    const token = await getToken();
    // Il backend conta i messaggi senza il benvenuto locale (indice 0 qui).
    await downloadMessageExport(sid, "docx", { messageIndex: bozzaIdx - 1, authToken: token ?? null });
  }

  const pannello = (
    <PannelloPratica
      scheda={scheda}
      onScheda={setScheda}
      bozza={bozza}
      onScaricaWord={bozza ? scaricaBozzaWord : undefined}
      fatti={fatti}
      fonti={fonti}
      competenze={usedSkills}
      documenti={documentiPratica}
      siti={analyzedUrls}
      onClose={() => setPannelloAperto(false)}
      className={
        pannelloAperto
          ? "fixed inset-0 z-50 xl:static xl:z-auto xl:w-[460px] xl:shrink-0 xl:border-l xl:border-[var(--line)]"
          : "hidden xl:flex xl:w-[460px] xl:shrink-0 xl:border-l xl:border-[var(--line)]"
      }
    />
  );

  if (authLoading) {
    return (
      <main className="flex min-h-screen items-center justify-center bg-[var(--bg-0)] text-sm text-[var(--text-muted)]">
        Caricamento…
      </main>
    );
  }

  if (!isSignedIn) {
    return <LoginFirstScreen />;
  }

  return (
    <div className="flex h-[100dvh] overflow-hidden bg-[var(--bg-1)] text-[var(--text-main)]">
      <Sidebar
        open={sidebarOpen}
        conversations={conversations}
        activeId={activeId}
        onSelect={(id) => {
          setActiveId(id);
          // Lazy-load messages reali della session backend la prima volta che
          // la conv viene aperta. Era bug: bootstrap mostrava titoli ma
          // messages restavano [WELCOME] vuoti → sembrava cronologia azzerata.
          const target = conversations.find((c) => c.id === id);
          const sessionId = target?.kbotSessionId;
          const isStubMessages = (target?.messages.length ?? 0) <= 1;
          if (sessionId && isStubMessages && isSignedIn) {
            void (async () => {
              try {
                const token = await getToken();
                if (!token) return;
                const sess = await getSession(sessionId, token);
                const backendMsgs = sess.messages || [];
                if (!backendMsgs.length) return;
                const mapped: ChatMessage[] = [
                  { id: uid("msg"), role: "assistant", content: WELCOME_MESSAGE, ts: 0 },
                  ...backendMsgs.map((m) => ({
                    id: uid("msg"),
                    role: (m.role === "user" ? "user" : "assistant") as "user" | "assistant",
                    content: typeof m.content === "string" ? m.content : "",
                    ts: Date.now(),
                  })),
                ];
                setConversations((prev) =>
                  prev.map((c) => (c.id === id ? { ...c, messages: mapped } : c)),
                );
              } catch {
                /* network fail = mantiene welcome locale */
              }
            })();
          }
        }}
        onNew={handleNewConversation}
        onDelete={handleDeleteConversation}
        onRename={handleRenameConversation}
        onClose={() => setSidebarOpen(false)}
      />

      <div className="relative flex min-w-0 flex-1 flex-col ">
        <ChatLayoutHeader
          titolo={activeConversation.title}
          sottotitolo={loading ? "K-BOT sta lavorando…" : undefined}
          onOpenSidebar={() => setSidebarOpen(true)}
          onOpenPannello={() => setPannelloAperto(true)}
          schedeConContenuto={(bozza ? 1 : 0) + (documentiPratica.length + analyzedUrls.length > 0 ? 1 : 0) + (Object.keys(fatti).length > 0 ? 1 : 0) + (fonti.length > 0 ? 1 : 0)}
          isSignedIn={isSignedIn}
        />

        <main className="scroll-premium flex-1 overflow-y-auto px-4 pb-6 pt-6 lg:px-8">
          <div className="mx-auto flex w-full max-w-3xl flex-col gap-4">
            <AnimatePresence>
              {activeConversation.messages.map((m, idx) => (
                <MessageBubble
                  key={m.id}
                  message={{ ...m, hasPaid }}
                  onCheckout={startCheckoutFromUI}
                  onGeneratePdf={() => generateReportPdfFromUI(m.id)}
                  onDownloadXlsx={async () => {
                    const sid = kbotSession?.id;
                    if (!sid) return;
                    try {
                      const token = await getToken();
                      await downloadDeliverableXlsx(sid, {
                        authToken: token ?? null,
                        testMode: !hasPaid,
                      });
                    } catch (e) {
                      setError(e instanceof Error ? e.message : "Errore export Excel");
                    }
                  }}
                  onFollowUp={handleFollowUpClick}
                  onOpenDraft={idx === bozzaIdx ? () => { setScheda("bozza"); setPannelloAperto(true); } : undefined}
                  getAuthToken={getToken}
                  messageIndex={idx}
                />
              ))}
            </AnimatePresence>
            {loading && <LoadingState reportProgress={pdfProgress} />}
            {/* Date.now() in render is a deliberate snapshot — the banner's
                onExpired callback nulls rateLimitUntil so subsequent renders
                will drop the banner. */}
            {/* eslint-disable-next-line react-hooks/purity */}
            {rateLimitUntil && rateLimitUntil > Date.now() && (
              <RateLimitBanner
                retryAt={rateLimitUntil}
                onExpired={() => setRateLimitUntil(null)}
              />
            )}
            {activeConversation.messages.length <= 2 && (
              <p className="px-4 text-center text-xs text-[var(--text-muted)]">
                Le tue pratiche restano salvate sul tuo account. K-BOT è una pre-consulenza:
                prima di agire fai rivedere le bozze al tuo professionista.
              </p>
            )}
            {/* Flusso ufficiale: quando il bot ha raccolto abbastanza (boost
                instradato), UN bottone genera il report. Niente form da riempire:
                gli input 8e sono auto-compilati dalla conversazione e dai file. */}
            {kbotSession?.id && reportReady && (kbotSession.boostSuggerito || suggestedBoost) && (
              <ReportGenerator
                sessionId={kbotSession.id}
                getAuthToken={getToken}
                boostLabel={suggestedBoost?.label ?? kbotSession.boostSuggeritoLabel ?? undefined}
                autoStart={reportReady}
              />
            )}
            {error && <p className="text-sm text-red-300">{error}</p>}
            <div ref={messagesEndRef} />
          </div>
        </main>

        <div className="px-4 lg:px-8">
          <div className="mx-auto w-full max-w-3xl">
            <Composer
              value={composer}
              onChange={setComposer}
              onSubmit={handleSubmit}
              disabled={
                loading ||
                fetchingUrl ||
                // eslint-disable-next-line react-hooks/purity
                (rateLimitUntil !== null && rateLimitUntil > Date.now())
              }
              suggestions={REPORT_SUGGESTIONS}
              onPickFiles={handleFilePick}
              files={pendingFiles}
              uploadingFiles={uploadingFiles}
              onFetchUrl={handleFetchUrl}
              fetchingUrl={fetchingUrl}
              analyzedUrls={analyzedUrls}
              onRemoveContext={handleRemoveContext}
            />
          </div>
        </div>

      </div>

      {pannello}
    </div>
  );
}
