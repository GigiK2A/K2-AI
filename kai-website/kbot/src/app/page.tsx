"use client";

import { useMemo, useState } from "react";
import { AnimatePresence } from "framer-motion";
import { ChatLayoutHeader } from "@/components/layout/ChatLayout";
import { Sidebar } from "@/components/layout/Sidebar";
import { Composer } from "@/components/chat/Composer";
import { MessageBubble } from "@/components/chat/MessageBubble";
import { LoadingState } from "@/components/chat/LoadingState";
import { InsightPanel } from "@/components/insights/InsightPanel";
import { fetchSkills, sendChat, uploadContextFiles } from "@/lib/api";
import { ChatMessage, Conversation, Mode, SkillSummary, UploadedFile } from "@/types/chat";
import { uid } from "@/lib/utils";
import { MessageCircle, UserCircle2 } from "lucide-react";
import { useEffect } from "react";
import { SignIn, SignInButton, useAuth, useUser, UserButton } from "@clerk/nextjs";
import { AuthGate } from "@/components/auth/AuthGate";
import { startCheckout, submitFeedback } from "@/lib/api";

const REPORT_SUGGESTIONS = ["Executive summary", "Piano operativo", "KPI", "Rischi"];

const clerkAppearance = {
  variables: {
    colorPrimary: "#14b8a6",
    colorBackground: "#0a0a0a",
    colorInputBackground: "#111111",
    colorInputText: "#e5e7eb",
    colorText: "#e5e7eb",
    colorTextSecondary: "#6b7280",
    borderRadius: "8px",
  },
  elements: {
    card: { boxShadow: "none", border: "1px solid #1f1f1f", background: "#050505" },
    formButtonPrimary: { background: "#14b8a6", color: "#000", fontWeight: "700" },
    socialButtonsBlockButton: { border: "1px solid #1f1f1f", background: "#111111", color: "#ffffff" },
    socialButtonsBlockButtonText: { color: "#ffffff" },
    dividerLine: { background: "#1f1f1f" },
    dividerText: { color: "#4b5563" },
    footerActionLink: { color: "#14b8a6" },
    headerTitle: { display: "none" },
    headerSubtitle: { display: "none" },
  },
};

function streamAppend(setter: (value: string) => void, text: string) {
  let idx = 0;
  const timer = setInterval(() => {
    idx += 28;
    setter(text.slice(0, idx));
    if (idx >= text.length) clearInterval(timer);
  }, 22);
}

function LoginFirstScreen() {
  return (
    <main className="flex min-h-screen items-center justify-center bg-[#050505] px-6 py-10 text-white">
      <div className="grid w-full max-w-5xl overflow-hidden rounded-2xl border border-[#111] bg-[#0a0a0a] md:grid-cols-[0.95fr_1fr]">
        <section
          className="hidden min-h-[640px] flex-col justify-between p-10 md:flex"
          style={{ background: "linear-gradient(160deg,#071f1d 0%,#050d0c 60%,#050505 100%)" }}
        >
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-[#14b8a6] font-black text-black">K</div>
            <span className="text-sm font-extrabold tracking-wide">K2-AI</span>
          </div>
          <div>
            <h1 className="text-3xl font-extrabold leading-tight">Accedi per generare report premium</h1>
            <p className="mt-3 max-w-sm text-sm leading-6 text-[#9ca3af]">
              La chat report si apre dopo il login, così download, dashboard e stato Premium restano collegati al tuo account.
            </p>
          </div>
          <p className="text-xs text-[#4b5563]">K2-AI - report professionali e analisi strategica.</p>
        </section>

        <section className="flex min-h-[640px] flex-col items-center justify-center px-6 py-10">
          <div className="mb-8 text-center md:hidden">
            <div className="mx-auto mb-3 flex h-10 w-10 items-center justify-center rounded-xl bg-[#14b8a6] font-black text-black">K</div>
            <p className="text-lg font-bold">K2-AI Report Premium</p>
          </div>
          <div className="w-full max-w-sm">
            <div className="mb-6">
              <h2 className="text-xl font-bold">Accedi al tuo account</h2>
              <p className="mt-1 text-sm text-[#6b7280]">Dopo l&apos;accesso si apre la chat K-BOT.</p>
            </div>
            <SignIn
              routing="hash"
              appearance={clerkAppearance}
              fallbackRedirectUrl="/app/"
              forceRedirectUrl="/app/"
              signUpUrl="/app/sign-up"
              fallback={<p className="text-sm text-[#6b7280]">Caricamento login...</p>}
            />
          </div>
        </section>
      </div>
    </main>
  );
}

export default function HomePage() {
  const [mode, setMode] = useState<Mode>("report");
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [loading, setLoading] = useState(false);
  const [composer, setComposer] = useState("");
  const [skills, setSkills] = useState<SkillSummary[]>([]);
  const [usedSkills, setUsedSkills] = useState<string[]>([]);
  const [activeSkills, setActiveSkills] = useState<string[]>([]);
  const [error, setError] = useState("");
  const [pendingFiles, setPendingFiles] = useState<UploadedFile[]>([]);
  const [contextFilesByConversation, setContextFilesByConversation] = useState<Record<string, UploadedFile[]>>({});

  const { getToken, isSignedIn } = useAuth();
  const { user } = useUser();
  const hasPaid = Boolean((user?.publicMetadata as { has_paid?: boolean })?.has_paid);

  const [conversations, setConversations] = useState<Conversation[]>([
    {
      id: uid("conv"),
      title: "Nuova conversazione",
      mode: "lead",
      messages: [
        {
          id: uid("msg"),
          role: "assistant",
          content: "Ciao, sono K2-AI. Posso guidarti su acquisizione clienti o generare report premium professionali.",
          ts: 0,
        },
      ],
    },
  ]);

  const [activeId, setActiveId] = useState(conversations[0].id);

  useEffect(() => {
    if (!isSignedIn) return;
    void fetchSkills().then(setSkills).catch(() => setSkills([]));
  }, [isSignedIn]);

  const activeConversation = useMemo(
    () => conversations.find((c) => c.id === activeId) ?? conversations[0],
    [conversations, activeId],
  );

  const suggestions = REPORT_SUGGESTIONS;

  function updateMessages(next: ChatMessage[]) {
    setConversations((prev) => prev.map((c) => (c.id === activeConversation.id ? { ...c, messages: next } : c)));
  }

  function handleNewConversation() {
    const newConv: Conversation = {
      id: uid("conv"),
      title: "Nuova chat",
      mode,
      messages: [],
    };
    setConversations((prev) => [newConv, ...prev]);
    setActiveId(newConv.id);
    setComposer("");
    setUsedSkills([]);
    setActiveSkills([]);
    setPendingFiles([]);
  }

  function getConversationContextFiles(conversationId: string): UploadedFile[] {
    return contextFilesByConversation[conversationId] ?? [];
  }

  async function handleFilePick(files: File[]) {
    setError("");
    try {
      const uploaded = await uploadContextFiles(files);
      setPendingFiles((prev) => [...prev, ...uploaded]);
      setContextFilesByConversation((prev) => ({
        ...prev,
        [activeConversation.id]: [...(prev[activeConversation.id] ?? []), ...uploaded],
      }));
    } catch (e) {
      setError(e instanceof Error ? e.message : "Errore upload file");
    }
  }

  async function handleSubmit() {
    if (!composer.trim() || loading) return;
    if (mode === "report" && !isSignedIn) return;

    setError("");
    setLoading(true);
    const userMessage: ChatMessage = { id: uid("msg"), role: "user", content: composer, ts: Date.now(), attachments: pendingFiles };
    const stubMessage: ChatMessage = { id: uid("msg"), role: "assistant", content: "", ts: Date.now() };
    const currentMessages = [...activeConversation.messages, userMessage, stubMessage];
    updateMessages(currentMessages);

    const prompt = composer;
    setComposer("");
    const filesForContext = getConversationContextFiles(activeConversation.id);
    setPendingFiles([]);

    try {
      const paid = mode === "lead" ? true : hasPaid;
      const authToken = mode === "report" ? await getToken() : null;
      const res = await sendChat(
        prompt,
        mode,
        paid,
        activeConversation.id,
        filesForContext.map((f) => f.fileId),
        authToken,
      );
      setUsedSkills(res.usedSkills);
      setActiveSkills(res.usedSkills);

      streamAppend((partial) => {
        updateMessages(
          currentMessages.map((m) =>
            m.id === stubMessage.id
              ? {
                  ...m,
                  content: partial,
                  reportPdfUrl: res.reportPdfUrl,
                  reportPdfDownloadUrl: res.reportPdfDownloadUrl,
                  reportPdfFilename: res.reportPdfFilename,
                  reportHtmlUrl: res.reportHtmlUrl,
                  reportHtmlDownloadUrl: res.reportHtmlDownloadUrl,
                }
              : m,
          ),
        );
      }, res.answer);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Errore imprevisto");
      updateMessages(activeConversation.messages);
    } finally {
      setLoading(false);
    }
  }

  if (!isSignedIn) {
    return <LoginFirstScreen />;
  }

  return (
    <div className="flex h-screen overflow-hidden bg-[var(--bg-0)] text-[var(--text-main)]">
      <Sidebar
        open={sidebarOpen}
        mode={mode}
        onMode={(m) => {
          setMode(m);
        }}
        conversations={conversations}
        activeId={activeId}
        onSelect={setActiveId}
        onNew={handleNewConversation}
        onClose={() => setSidebarOpen(false)}
      />

      <div className="relative flex min-w-0 flex-1 flex-col">
        <ChatLayoutHeader
          mode={mode}
          usedSkills={usedSkills}
          activeSkills={activeSkills}
          loading={loading}
          onOpenSidebar={() => setSidebarOpen(true)}
          isSignedIn={isSignedIn}
        />

        <main className="scroll-premium flex-1 overflow-y-auto px-4 pb-24 pt-6 lg:px-8">
          <div className="mx-auto flex w-full max-w-4xl flex-col gap-4">
            <AuthGate>
              <AnimatePresence>
                {activeConversation.messages.map((m) => (
                  <MessageBubble
                    key={m.id}
                    message={{ ...m, hasPaid }}
                    onCheckout={async () => {
                      const token = await getToken();
                      if (token) { const url = await startCheckout(token); window.location.href = url; }
                    }}
                    onFeedback={async (reportId, rating, comment) => {
                      const token = await getToken();
                      if (token) await submitFeedback(reportId, rating, comment, token);
                    }}
                  />
                ))}
              </AnimatePresence>
              {loading && <LoadingState />}
            </AuthGate>
            {activeConversation.messages.length <= 2 && (
              <p className="px-4 text-center text-xs text-[var(--text-muted)]">
                Le tue conversazioni vengono salvate per continuare da dove hai lasciato. I documenti generati non vengono conservati sui nostri server.
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
              disabled={loading}
              suggestions={suggestions}
              onPickFiles={handleFilePick}
              files={pendingFiles}
            />
          </div>
        </div>

        <nav className="fixed inset-x-0 bottom-0 z-30 border-t border-[var(--line)] bg-[rgba(5,5,5,0.95)] px-4 py-2 xl:hidden">
          <div className="mx-auto flex max-w-xl items-center justify-around text-xs text-[var(--text-soft)]">
            <button className="flex flex-col items-center gap-1 text-[var(--teal)]"><MessageCircle size={16} />Chat</button>
            {isSignedIn ? (
              <div className="flex flex-col items-center gap-1">
                <UserButton />
                <span>Account</span>
              </div>
            ) : (
              <SignInButton mode="modal">
                <button className="flex flex-col items-center gap-1">
                  <UserCircle2 size={16} />Account
                </button>
              </SignInButton>
            )}
          </div>
        </nav>
      </div>

      <InsightPanel mode={mode} usedSkills={usedSkills} availableSkills={skills} onLeadSave={async () => {}} />
    </div>
  );
}
