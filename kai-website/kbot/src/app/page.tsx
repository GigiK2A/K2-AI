"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { AnimatePresence } from "framer-motion";
import { ChatLayoutHeader } from "@/components/layout/ChatLayout";
import { Sidebar } from "@/components/layout/Sidebar";
import { Composer } from "@/components/chat/Composer";
import { MessageBubble } from "@/components/chat/MessageBubble";
import { LoadingState } from "@/components/chat/LoadingState";
import { InsightPanel } from "@/components/insights/InsightPanel";
import {
  sendMessage,
  streamMessage,
  uploadFiles,
  startCheckout,
  generatePdfStream,
  getSession,
  fetchUrl,
  listConversations,
  createRemoteConversation,
  updateRemoteConversation,
  deleteRemoteConversation,
  removeContextItem,
  fetchFollowUps,
  RateLimitError,
  type UploadedFile,
  type AnalyzedUrl,
} from "@/lib/api";
import { RateLimitBanner } from "@/components/chat/RateLimitBanner";
import { track } from "@/lib/analytics";
import { ChatMessage, Conversation, Mode } from "@/types/chat";
import { uid } from "@/lib/utils";
import { MessageCircle } from "lucide-react";
import { AuthForm } from "@/components/auth/AuthForm";
import { AccountButton } from "@/components/auth/AccountButton";
import { useKbotAuth } from "@/app/providers";

const REPORT_SUGGESTIONS = [
  "Voglio un audit operativo per la mia PMI",
  "Analisi strategia marketing per il mio settore",
  "Audit SEO del mio sito",
  "Valutazione tecnica di un nuovo progetto",
];

const WELCOME_MESSAGE =
  "Benvenuto. Sono K-BOT, l'analista K2-AI. Insieme produciamo un report operativo concreto sul tuo caso. Per partire, dimmi che tipo di analisi vuoi: operativa, marketing, SEO, bilancio, fattibilità tecnica, oppure descrivi liberamente il tuo problema.\n\n_Privacy: la conversazione viene processata da Claude (Anthropic, US) per generare il report. Dettagli su /privacy._";

function LoginFirstScreen() {
  return (
    <main className="flex min-h-screen items-center justify-center bg-[#050505] px-6 py-10 text-white">
      <div className="grid w-full max-w-5xl overflow-hidden rounded-2xl border border-[#111] bg-[#0a0a0a] md:grid-cols-[0.95fr_1fr]">
        <section
          className="hidden min-h-[640px] flex-col justify-between p-10 md:flex"
          style={{ background: "linear-gradient(160deg,#071f1d 0%,#050d0c 60%,#050505 100%)" }}
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
              Accedi per generare report premium
            </h1>
            <p className="mt-3 max-w-sm text-sm leading-6 text-[#9ca3af]">
              La chat K-BOT si apre dopo il login: download, dashboard e stato Premium
              restano collegati al tuo account.
            </p>
          </div>
          <p className="text-xs text-[#4b5563]">
            K2-AI · report professionali e analisi strategica.
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
            <p className="text-lg font-bold">Report Premium</p>
          </div>
          <div className="w-full max-w-sm">
            <div className="mb-6">
              <h2 className="text-xl font-bold">Accedi al tuo account</h2>
              <p className="mt-1 text-sm text-[#6b7280]">
                Dopo l&apos;accesso si apre la chat K-BOT.
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
  const { loading: authLoading, getToken, isSignedIn, hasPaid, ensureSession, resetSession, kbotSession } =
    useKbotAuth();

  const [mode, setMode] = useState<Mode>("report");
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [loading, setLoading] = useState(false);
  const [composer, setComposer] = useState("");
  const [usedSkills, setUsedSkills] = useState<string[]>([]);
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
  const [forcedSkills, setForcedSkills] = useState<string[]>([]);
  const [rateLimitUntil, setRateLimitUntil] = useState<number | null>(null);
  const [pdfProgress, setPdfProgress] = useState<{ stage: string; progress: number } | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Track kbot_open once the chat surface mounts for an authenticated user.
  useEffect(() => {
    if (!authLoading && isSignedIn) {
      track("kbot_open", { surface: "kbot_app" });
    }
  }, [authLoading, isSignedIn]);

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
        const mapped: Conversation[] = remote.map((r) => ({
          id: r.id,
          remoteId: r.id,
          title: r.title || "Nuova conversazione",
          mode: r.mode,
          kbotSessionId: r.kbotSessionId,
          messages: [{ id: uid("msg"), role: "assistant", content: WELCOME_MESSAGE, ts: 0 }],
        }));
        setConversations(mapped);
        setActiveId(mapped[0].id);
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

  const [conversations, setConversations] = useState<Conversation[]>([
    {
      id: uid("conv"),
      title: "Nuova conversazione",
      mode: "report",
      messages: [
        { id: uid("msg"), role: "assistant", content: WELCOME_MESSAGE, ts: 0 },
      ],
    },
  ]);
  const [activeId, setActiveId] = useState(conversations[0].id);

  /* Cross-bot bridge: when arriving from suite-ai widget with ?continue=<id>,
     adopt that session id instead of creating a new one. Stripped after read
     so a refresh doesn't keep forcing the bridge. */
  useEffect(() => {
    if (typeof window === "undefined") return;
    const url = new URL(window.location.href);
    const carry = url.searchParams.get("continue") || url.searchParams.get("kbot_session");
    if (!carry) return;
    void ensureSession({ mode: "report", adopt: carry });
    url.searchParams.delete("continue");
    url.searchParams.delete("kbot_session");
    window.history.replaceState({}, "", url.toString());
  }, [ensureSession]);

  const activeConversation = useMemo(
    () => conversations.find((c) => c.id === activeId) ?? conversations[0],
    [conversations, activeId],
  );

  // Auto-scroll to bottom on new messages / streaming deltas / loading state.
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [activeConversation.messages.length, activeConversation.messages.at(-1)?.content, loading]);

  /* Per-conversation backend session: each sidebar conv must talk to its OWN
     kbot_sessions row, otherwise switching/creating conversations leaks
     uploaded_files + analyzed_urls across topics (Juventus + k2-ai.it mix). */
  useEffect(() => {
    const convSid = activeConversation.kbotSessionId ?? null;
    const liveSid = kbotSession?.id ?? null;
    if (convSid && convSid !== liveSid) {
      // Switch backend session to the one bound to this conversation.
      resetSession();
      void ensureSession({ mode: activeConversation.mode, adopt: convSid });
    } else if (!convSid && liveSid) {
      // New conv with no backend session yet — drop any stale one.
      resetSession();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activeConversation.id]);

  /* Bind backend session id back to the active conversation once known. */
  useEffect(() => {
    if (!kbotSession?.id) return;
    let remoteIdToSync: string | null | undefined;
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

  /** Imposta titolo conv se ancora generico ("Nuova chat" / "Nuova conversazione"). */
  function maybeSetTitle(label: string) {
    const clean = label.trim().replace(/\s+/g, " ").slice(0, 48);
    if (!clean) return;
    let updatedRemoteId: string | null | undefined;
    setConversations((prev) =>
      prev.map((c) => {
        if (c.id !== activeConversation.id) return c;
        const isGeneric = !c.title || /^Nuova (chat|conversazione)$/i.test(c.title);
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

  function toggleForcedSkill(name: string) {
    setForcedSkills((prev) =>
      prev.includes(name) ? prev.filter((s) => s !== name) : [...prev, name],
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
            title: "Nuova chat",
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
      title: "Nuova chat",
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
            title: "Nuova chat",
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
        const confirmMsg: ChatMessage = {
          id: uid("msg"),
          role: "assistant",
          content: `Ho analizzato **${result.title || url}** — il contenuto è disponibile per la nostra conversazione. Cosa vuoi sapere?`,
          ts: Date.now(),
        };
        updateMessages([...activeConversation.messages, confirmMsg]);
      } catch (err: unknown) {
        const errMsg: ChatMessage = {
          id: uid("msg"),
          role: "assistant",
          content: `Non riesco ad analizzare l'URL: ${err instanceof Error ? err.message : "errore sconosciuto"}.`,
          ts: Date.now(),
        };
        updateMessages([...activeConversation.messages, errMsg]);
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
          patchStub({
            content: res.message,
            reportReady: res.nextAction === "show_summary",
            sessionId: session.id,
          });
        },
      });

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

  if (authLoading) {
    return (
      <main className="flex min-h-screen items-center justify-center bg-[#050505] text-sm text-[#6b7280]">
        Caricamento…
      </main>
    );
  }

  if (!isSignedIn) {
    return <LoginFirstScreen />;
  }

  return (
    <div className="flex h-screen overflow-hidden bg-[var(--bg-0)] text-[var(--text-main)]">
      <Sidebar
        open={sidebarOpen}
        mode={mode}
        onMode={(m) => setMode(m)}
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

      <div className="relative flex min-w-0 flex-1 flex-col">
        <ChatLayoutHeader
          mode={mode}
          usedSkills={usedSkills}
          activeSkills={usedSkills}
          loading={loading}
          onOpenSidebar={() => setSidebarOpen(true)}
          isSignedIn={isSignedIn}
        />

        <main className="scroll-premium flex-1 overflow-y-auto px-4 pb-24 pt-6 lg:px-8">
          <div className="mx-auto flex w-full max-w-4xl flex-col gap-4">
            <AnimatePresence>
              {activeConversation.messages.map((m, idx) => (
                <MessageBubble
                  key={m.id}
                  message={{ ...m, hasPaid }}
                  onCheckout={startCheckoutFromUI}
                  onGeneratePdf={() => generateReportPdfFromUI(m.id)}
                  onFollowUp={handleFollowUpClick}
                  getAuthToken={getToken}
                  messageIndex={idx}
                />
              ))}
            </AnimatePresence>
            {loading && <LoadingState reportProgress={pdfProgress} />}
            {rateLimitUntil && rateLimitUntil > Date.now() && (
              <RateLimitBanner
                retryAt={rateLimitUntil}
                onExpired={() => setRateLimitUntil(null)}
              />
            )}
            {activeConversation.messages.length <= 2 && (
              <p className="px-4 text-center text-xs text-[var(--text-muted)]">
                Le tue conversazioni vengono salvate sul tuo account. I documenti generati
                restano disponibili in dashboard.
              </p>
            )}
            {error && <p className="text-sm text-red-300">{error}</p>}
            <div ref={messagesEndRef} />
          </div>
        </main>

        <div className="px-4 lg:px-8">
          <div className="mx-auto w-full max-w-4xl">
            <Composer
              value={composer}
              onChange={setComposer}
              onSubmit={handleSubmit}
              disabled={
                loading ||
                fetchingUrl ||
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

        <nav className="fixed inset-x-0 bottom-0 z-30 border-t border-[var(--line)] bg-[var(--bg-0)]/95 px-4 py-2 backdrop-blur xl:hidden">
          <div className="mx-auto flex max-w-xl items-center justify-around text-xs text-[var(--text-soft)]">
            <button className="flex flex-col items-center gap-1 text-[var(--teal)]">
              <MessageCircle size={16} />Chat
            </button>
            <AccountButton compact />
          </div>
        </nav>
      </div>

      <InsightPanel
        mode={mode}
        usedSkills={usedSkills}
        forcedSkills={forcedSkills}
        onToggleForcedSkill={toggleForcedSkill}
      />
    </div>
  );
}
