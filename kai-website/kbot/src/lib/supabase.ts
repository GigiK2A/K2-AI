import { createClient } from "@supabase/supabase-js";

const defaultSupabaseUrl = "https://uiuvwzrmrdqbfajguuab.supabase.co";
const defaultSupabasePublishableKey = "sb_publishable_uK5-KEElWk_Y8xOKUO0VYw_nHZ30lcM";

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL ?? defaultSupabaseUrl;
const supabaseAnonKey =
  process.env.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY ??
  process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY ??
  process.env.NEXT_PUBLIC_SUPABASE_KEY ??
  defaultSupabasePublishableKey;

export const isSupabaseAuthConfigured = Boolean(supabaseUrl && supabaseAnonKey);

export const supabase = createClient(supabaseUrl || "https://placeholder.supabase.co", supabaseAnonKey || "placeholder", {
  auth: {
    persistSession: true,
    autoRefreshToken: true,
    detectSessionInUrl: true,
  },
});
