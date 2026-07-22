"use client";

import { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState } from "react";
import type { Session, User } from "@supabase/supabase-js";
import { isSupabaseAuthConfigured, supabase } from "@/lib/supabase";
import { createSession, getSession, linkSessionToUser, type KbotSession, type Mode } from "@/lib/api";
import { initAnalytics } from "@/lib/analytics";

const STORAGE_KEY = "kbot.session_id";

export type SignUpProfile = {
  firstName: string;
  lastName: string;
  workSector: string;
  companyName?: string;
  privacyAccepted: boolean;
  termsAccepted: boolean;
  marketingAccepted: boolean;
};

type AppContextValue = {
  /* auth */
  configured: boolean;
  loading: boolean;
  user: User | null;
  session: Session | null;
  isSignedIn: boolean;
  hasPaid: boolean;
  getToken: () => Promise<string | null>;
  signIn: (email: string, password: string) => Promise<void>;
  signUp: (email: string, password: string, profile: SignUpProfile) => Promise<void>;
  signOut: () => Promise<void>;
  resetPassword: (email: string) => Promise<void>;
  updatePassword: (password: string) => Promise<void>;
  /* kbot session */
  kbotSessionId: string | null;
  kbotSession: KbotSession | null;
  ensureSession: (opts?: { mode?: Mode; serviceId?: string; adopt?: string; tagPillar?: string | null }) => Promise<KbotSession>;
  resetSession: () => void;
};

const AppContext = createContext<AppContextValue | null>(null);

function readHasPaid(user: User | null): boolean {
  if (!user) return false;
  const metadata = {
    ...(user.app_metadata ?? {}),
    ...(user.user_metadata ?? {}),
  } as { has_paid?: unknown; premium?: unknown };
  return (
    metadata.has_paid === true ||
    metadata.has_paid === "true" ||
    metadata.premium === true ||
    metadata.premium === "true"
  );
}

export function Providers({ children }: { children: React.ReactNode }) {
  const [session, setSession] = useState<Session | null>(null);
  const [loading, setLoading] = useState(isSupabaseAuthConfigured);
  const [kbotSession, setKbotSession] = useState<KbotSession | null>(null);
  const linkingRef = useRef<string | null>(null);

  /* ---------- Analytics bootstrap (anonymous, no cookies) ---------- */
  useEffect(() => {
    void initAnalytics();
  }, []);

  /* ---------- Supabase auth bootstrap ---------- */
  useEffect(() => {
    if (!isSupabaseAuthConfigured) return;

    let mounted = true;
    supabase.auth.getSession().then(({ data }) => {
      if (!mounted) return;
      setSession(data.session ?? null);
      setLoading(false);
    });

    const { data: listener } = supabase.auth.onAuthStateChange((_event, nextSession) => {
      setSession(nextSession);
      setLoading(false);
    });

    return () => {
      mounted = false;
      listener.subscription.unsubscribe();
    };
  }, []);

  const getToken = useCallback(async () => {
    if (!isSupabaseAuthConfigured) return null;
    const { data } = await supabase.auth.getSession();
    return data.session?.access_token ?? null;
  }, []);

  const signIn = useCallback(async (email: string, password: string) => {
    const { error } = await supabase.auth.signInWithPassword({ email, password });
    if (error) throw error;
  }, []);

  const signUp = useCallback(async (email: string, password: string, profile: SignUpProfile) => {
    const redirectTo =
      typeof window !== "undefined"
        ? `${window.location.origin}/app/`
        : undefined;
    const { error } = await supabase.auth.signUp({
      email,
      password,
      options: {
        emailRedirectTo: redirectTo,
        data: {
          first_name: profile.firstName,
          last_name: profile.lastName,
          full_name: `${profile.firstName} ${profile.lastName}`.trim(),
          work_sector: profile.workSector,
          company_name: profile.companyName || null,
          privacy_accepted: profile.privacyAccepted,
          terms_accepted: profile.termsAccepted,
          marketing_accepted: profile.marketingAccepted,
          privacy_accepted_at: profile.privacyAccepted ? new Date().toISOString() : null,
          terms_accepted_at: profile.termsAccepted ? new Date().toISOString() : null,
          marketing_accepted_at: profile.marketingAccepted ? new Date().toISOString() : null,
        },
      },
    });
    if (error) throw error;
  }, []);

  const signOut = useCallback(async () => {
    await supabase.auth.signOut();
  }, []);

  /* Invia l'email con il link di recupero. redirectTo DEVE essere nell'allowlist
     Supabase (Auth → URL Configuration → Redirect URLs). */
  const resetPassword = useCallback(async (email: string) => {
    const redirectTo =
      typeof window !== "undefined"
        ? `${window.location.origin}/app/reset-password`
        : undefined;
    const { error } = await supabase.auth.resetPasswordForEmail(email, { redirectTo });
    if (error) throw error;
  }, []);

  /* Imposta la nuova password. Richiede una sessione di recupero attiva (creata da
     detectSessionInUrl quando l'utente arriva dal link email → evento PASSWORD_RECOVERY). */
  const updatePassword = useCallback(async (password: string) => {
    const { error } = await supabase.auth.updateUser({ password });
    if (error) throw error;
  }, []);

  /* ---------- Kbot session lifecycle ---------- */
  const persistSessionId = useCallback((id: string | null) => {
    if (typeof window === "undefined") return;
    if (id) window.localStorage.setItem(STORAGE_KEY, id);
    else window.localStorage.removeItem(STORAGE_KEY);
  }, []);

  const ensureSession = useCallback(
    async (opts?: { mode?: Mode; serviceId?: string; adopt?: string; tagPillar?: string | null }) => {
      if (kbotSession) return kbotSession;
      const token = await getToken();
      // Priority: explicit adopt (cross-bot bridge from suite-ai) > localStorage > fresh.
      const adopted = opts?.adopt?.trim();
      const stored =
        adopted ||
        (typeof window !== "undefined" ? window.localStorage.getItem(STORAGE_KEY) : null);
      if (stored) {
        // Restore della sessione REALE (bug "chat persa al refresh"): il backend ha già
        // tutta la cronologia su Supabase — la fetchiamo così la UI può re-idratare i
        // messaggi. Se la sessione non esiste più (404/scaduta) si riparte pulita.
        try {
          const real = await getSession(stored, token);
          if (real?.id) {
            setKbotSession(real);
            persistSessionId(real.id);
            return real;
          }
        } catch (err) {
          // sessione morta o di un altro utente → dimentica l'id e crea fresh.
          const msg = String(err instanceof Error ? err.message : err).toLowerCase();
          if (msg.includes("404") || msg.includes("403") || msg.includes("not found") ||
              msg.includes("non trovata") || msg.includes("not your session")) {
            persistSessionId(null);
          } else {
            // errore di rete transitorio: placeholder col solo id (comportamento storico)
            const placeholder: KbotSession = {
              id: stored,
              serviceId: opts?.serviceId ?? null,
              mode: opts?.mode ?? "report",
              messages: [],
              extractedData: {},
              summary: null,
              recommendedServiceId: null,
              recommendedServiceName: null,
              recommendedTier: null,
              status: "active",
              pdfUrl: null,
              hasUser: false,
              timestamps: { createdAt: new Date().toISOString(), updatedAt: new Date().toISOString() },
            };
            setKbotSession(placeholder);
            return placeholder;
          }
        }
      }
      const fresh = await createSession({
        mode: opts?.mode ?? "report",
        serviceId: opts?.serviceId,
        tagPillar: opts?.tagPillar,
        authToken: token,
      });
      setKbotSession(fresh);
      persistSessionId(fresh.id);
      return fresh;
    },
    [getToken, kbotSession, persistSessionId],
  );

  const resetSession = useCallback(() => {
    setKbotSession(null);
    persistSessionId(null);
  }, [persistSessionId]);

  /* When the user signs in and there's an unlinked anon session, link it. */
  useEffect(() => {
    const user = session?.user;
    if (!user || !kbotSession || kbotSession.hasUser) return;
    if (linkingRef.current === kbotSession.id) return;
    linkingRef.current = kbotSession.id;
    (async () => {
      const token = await getToken();
      if (!token) return;
      try {
        const linked = await linkSessionToUser(kbotSession.id, token, kbotSession.linkToken);
        setKbotSession(linked);
      } catch (err) {
        // 409 = already linked to a different user; drop our stale id so a fresh anon session can start.
        console.warn("link session failed:", err);
        if (String(err).includes("409") || String(err).toLowerCase().includes("already linked")) {
          resetSession();
        }
      } finally {
        linkingRef.current = null;
      }
    })();
  }, [getToken, kbotSession, resetSession, session]);

  const value = useMemo<AppContextValue>(() => {
    const user = session?.user ?? null;
    return {
      configured: isSupabaseAuthConfigured,
      loading,
      user,
      session,
      isSignedIn: Boolean(user),
      hasPaid: readHasPaid(user),
      getToken,
      signIn,
      signUp,
      signOut,
      resetPassword,
      updatePassword,
      kbotSessionId: kbotSession?.id ?? null,
      kbotSession,
      ensureSession,
      resetSession,
    };
  }, [
    ensureSession,
    getToken,
    kbotSession,
    loading,
    resetSession,
    resetPassword,
    updatePassword,
    session,
    signIn,
    signOut,
    signUp,
  ]);

  return <AppContext.Provider value={value}>{children}</AppContext.Provider>;
}

export function useKbotAuth() {
  const value = useContext(AppContext);
  if (!value) throw new Error("useKbotAuth must be used inside Providers");
  return value;
}
