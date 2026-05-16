"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { AnimatePresence } from "framer-motion";
import { ChatLayoutHeader } from "@/components/layout/ChatLayout";
import { Sidebar } from "@/components/layout/Sidebar";
import { Composer } from "@/components/chat/Composer";
import { MessageBubble } from "@/components/chat/MessageBubble";
import { LoadingState } from "@/components/chat/LoadingState";
import { InsightPanel } from "@/components/insights/InsightPanel";
import { sendMessage, uploadFiles, startCheckout, fetchUrl, type UploadedFile, type AnalyzedUrl } from "@/lib/api";
import { track } from "@/lib/analytics";
import { ChatMessage, Conversation, Mode } from "@/types/chat";
import { uid } from "@/lib/utils";
import { MessageCircle } from "lucide-react";
import { AuthForm } from "@/components/auth/AuthForm";
import { AccountButton } from "@/components/auth/AccountButton";
import { useKbotAuth } from "@/app/providers";

const REPORT_SUGGESTIONS = [
  "Automatizzare il triage delle email in arrivo",
  "Un agente AI che risponde ai ticket di assistenza",
  "Una microapp interna per pratiche tecniche",
  "Un assistente che cerca nei nostri documenti",
];

const WELCOME_MESSAGE =
  "Ciao, sono K-BOT di K2-AI. Raccontami in 2-3 righe il processo che ti costa più tempo: cosa succede oggi, dove si blocca, quali strumenti usi già. Da lì capiamo se l'AI può togliere lavoro ripetitivo al tuo team e che intervento ha senso.";

function LoginFirstScreen() {
  return (
    <main className="flex min-h-screen items-center justify-center bg-[#050505] px-6 py-10 text-white">
      <div className="grid w-full max-w-5xl overflow-hidden rounded-2xl border border-[#111] bg-[#0a0a0a] md:grid-cols-[0.95fr_1fr]">
        <section
          className="hidden min-h-[640px] flex-col justify-between p-10 md:flex"
          style={{ background: "linear-gradient(160deg,#071f1d 0%,#050d0c 60%,#050505 100%)" }}
        >
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-[#14b8a6] font-black text-black">
              K
            </div>
            <span className="text-sm font-extrabold tracking-wide">K2-AI</span>
          </div>
          <div>
            <h1 className="text-3xl font-extrabold leading-tight">
              Accedi a K-BOT
            </h1>
            <p className="mt-3 max-w-sm text-sm leading-6 text-[#9ca3af]">
              Descrivi il processo che vuoi automatizzare. K-BOT capisce il caso,
              propone un intervento concreto e tiene tutto collegato al tuo account.
            </p>
          </div>
          <p className="text-xs text-[#4b5563]">
            K2-AI · sistemi AI operativi per PMI italiane.
          </p>
        </section>

        <section className="flex min-h-[640px] flex-col items-center justify-center px-6 py-10">
          <div className="mb-8 text-center md:hidden">
            <div className="mx-auto mb-3 flex h-10 w-10 items-center justify-center rounded-xl bg-[#14b8a6] font-black text-black">
              K
            </div>
            <p className="text-lg font-bold">K2-AI Report Premium</p>
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
  const { loading: authLoading, getToken, isSignedIn, hasPaid, ensureSession, resetSession } =
    useKbotAuth();

  const [mode, setMode] = useState<Mode>("report");
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [loading, setLoading] = useState(false);
  const [composer, setComposer] = useState("");
  const [usedSkills, setUsedSkills] = useState<string[]>([]);
  const [error, setError] = useState("");
  const [pendingFiles, setPendingFiles] = useState<UploadedFile[]>([]);
  const [contextFilesByConversation, setContextFilesByConversation] = useState<
    Record<string, UploadedFile[]>
  >({});
  const [fetchingUrl, setFetchingUrl] = useState(false);
  const [analyzedUrls, setAnalyzedUrls] = useState<AnalyzedUrl[]>([]);

  // Track kbot_open once the chat surface mounts for an authenticated user.
  useEffect(() => {
    if (!authLoading && isSignedIn) {
      track("kbot_open", { surface: "kbot_app" });
    }
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

  function updateMessages(next: ChatMessage[]) {
    setConversations((prev) =>
      prev.map((c) => (c.id === activeConversation.id ? { ...c, messages: next } : c)),
    );
  }

  function handleDeleteConversation(convId: string) {
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
  }

  function handleNewConversation() {
    resetSession(); // start a fresh kbot_sessions row on the next message
    const newConv: Conversation = {
      id: uid("conv"),
      title: "Nuova chat",
      mode,
      messages: [
        { id: uid("msg"), role: "assistant", content: WELCOME_MESSAGE, ts: 0 },
      ],
    };
    setConversations((prev) => [newConv, ...prev]);
    setActiveId(newConv.id);
    setComposer("");
    setUsedSkills([]);
    setPendingFiles([]);
  }

  const handleFilePick = useCallback(
    async (files: File[]) => {
      setError("");
      try {
        const session = await ensureSession({ mode });
        const token = await getToken();
        const uploaded = await uploadFiles(session.id, files, token);
        setPendingFiles((prev) => [...prev, ...uploaded]);
        setContextFilesByConversation((prev) => ({
          ...prev,
          [activeConversation.id]: [...(prev[activeConversation.id] ?? []), ...uploaded],
        }));
      } catch (e) {
        setError(e instanceof Error ? e.message : "Errore upload file");
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

  async function handleSubmit() {
    if (!composer.trim() || loading) return;

    setError("");
    setLoading(true);
    const userMessage: ChatMessage = {
      id: uid("msg"),
      role: "user",
      content: composer,
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

    const prompt = composer;
    track("kbot_message_sent", { length: prompt.length, mode });
    setComposer("");
    setPendingFiles([]);

    try {
      const session = await ensureSession({ mode });
      const token = await getToken();
      const res = await sendMessage(session.id, prompt, { authToken: token });
      const skills = (res.session?.extractedData as { used_skills?: string[] } | undefined)?.used_skills ?? [];
      setUsedSkills(skills);

      updateMessages(
        currentMessages.map((m) =>
          m.id === stubMessage.id
            ? {
                ...m,
                content: res.message,
                reportReady: res.nextAction === "show_summary",
                sessionId: session.id,
              }
            : m,
        ),
      );
    } catch (e) {
      setError(e instanceof Error ? e.message : "Errore imprevisto");
      updateMessages(activeConversation.messages);
    } finally {
      setLoading(false);
    }
  }

  async function startCheckoutFromUI() {
    const session = await ensureSession({ mode });
    track("kbot_report_requested", { mode });
    const token = await getToken();
    if (!token) return;
    const url = await startCheckout(session.id, token);
    window.location.href = url;
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
        onSelect={setActiveId}
        onNew={handleNewConversation}
        onDelete={handleDeleteConversation}
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
              {activeConversation.messages.map((m) => (
                <MessageBubble
                  key={m.id}
                  message={{ ...m, hasPaid }}
                  onCheckout={startCheckoutFromUI}
                />
              ))}
            </AnimatePresence>
            {loading && <LoadingState />}
            {activeConversation.messages.length <= 2 && (
              <p className="px-4 text-center text-xs text-[var(--text-muted)]">
                Le tue conversazioni vengono salvate sul tuo account. I documenti generati
                restano disponibili in dashboard.
              </p>
            )}
            {error && <p className="text-sm text-red-300">{error}</p>}
          </div>
        </main>

        <div className="px-4 lg:px-8">
          <div className="mx-auto w-full max-w-4xl">
            <Composer
              value={composer}
              onChange={setComposer}
              onSubmit={handleSubmit}
              disabled={loading || fetchingUrl}
              suggestions={REPORT_SUGGESTIONS}
              onPickFiles={handleFilePick}
              files={pendingFiles}
              onFetchUrl={handleFetchUrl}
              fetchingUrl={fetchingUrl}
            />
          </div>
        </div>

        <nav className="fixed inset-x-0 bottom-0 z-30 border-t border-[var(--line)] bg-[rgba(5,5,5,0.95)] px-4 py-2 xl:hidden">
          <div className="mx-auto flex max-w-xl items-center justify-around text-xs text-[var(--text-soft)]">
            <button className="flex flex-col items-center gap-1 text-[var(--teal)]">
              <MessageCircle size={16} />Chat
            </button>
            <AccountButton compact />
          </div>
        </nav>
      </div>

      <InsightPanel mode={mode} usedSkills={usedSkills} availableSkills={[]} onLeadSave={async () => {}} />
    </div>
  );
}
