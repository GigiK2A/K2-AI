import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  basePath: '/app',
  assetPrefix: '/app',
  output: 'standalone',
  outputFileTracingRoot: process.cwd(),
  trailingSlash: true,
  env: {
    // ATTENZIONE: tutto ciò che sta qui viene INLINATO nel bundle servito al
    // browser. Nessun fallback su nomi ambigui: `SUPABASE_KEY` altrove in questa
    // repo è un alias della SERVICE-ROLE key (server.js, api/kbot/_shared.ts,
    // backend/app/settings.py). Se finisse in fondo a questa catena, una build
    // fatta con l'env di runtime spedirebbe a ogni browser una chiave che bypassa
    // la RLS. Qui si accettano solo variabili già dichiarate come pubbliche.
    NEXT_PUBLIC_SUPABASE_URL: process.env.NEXT_PUBLIC_SUPABASE_URL || process.env.SUPABASE_URL || '',
    NEXT_PUBLIC_SUPABASE_ANON_KEY:
      process.env.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY ||
      process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY ||
      process.env.NEXT_PUBLIC_SUPABASE_KEY ||
      '',
    NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY:
      process.env.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY ||
      process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY ||
      process.env.NEXT_PUBLIC_SUPABASE_KEY ||
      '',
  },
  images: { unoptimized: true },
};

export default nextConfig;
