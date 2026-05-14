"use client";

import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import type { Session, User } from "@supabase/supabase-js";
import { isSupabaseAuthConfigured, supabase } from "@/lib/supabase";

type AuthContextValue = {
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
};

const AuthContext = createContext<AuthContextValue | null>(null);

export type SignUpProfile = {
  firstName: string;
  lastName: string;
  workSector: string;
  companyName?: string;
  privacyAccepted: boolean;
  termsAccepted: boolean;
  marketingAccepted: boolean;
};

function readHasPaid(user: User | null) {
  if (!user) return false;
  const metadata = {
    ...(user.app_metadata ?? {}),
    ...(user.user_metadata ?? {}),
  } as { has_paid?: unknown; premium?: unknown };
  return metadata.has_paid === true || metadata.has_paid === "true" || metadata.premium === true || metadata.premium === "true";
}

export function Providers({ children }: { children: React.ReactNode }) {
  const [session, setSession] = useState<Session | null>(null);
  const [loading, setLoading] = useState(isSupabaseAuthConfigured);

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
    const { error } = await supabase.auth.signUp({
      email,
      password,
      options: {
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

  const value = useMemo<AuthContextValue>(() => {
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
    };
  }, [getToken, loading, session, signIn, signOut, signUp]);

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useKbotAuth() {
  const value = useContext(AuthContext);
  if (!value) throw new Error("useKbotAuth must be used inside Providers");
  return value;
}
