import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  basePath: '/app',
  assetPrefix: '/app',
  output: 'standalone',
  outputFileTracingRoot: process.cwd(),
  trailingSlash: true,
  env: {
    NEXT_PUBLIC_SUPABASE_URL: process.env.NEXT_PUBLIC_SUPABASE_URL || process.env.SUPABASE_URL || '',
    NEXT_PUBLIC_SUPABASE_ANON_KEY:
      process.env.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY ||
      process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY ||
      process.env.NEXT_PUBLIC_SUPABASE_KEY ||
      process.env.SUPABASE_ANON_KEY ||
      process.env.SUPABASE_KEY ||
      '',
    NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY:
      process.env.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY ||
      process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY ||
      process.env.NEXT_PUBLIC_SUPABASE_KEY ||
      process.env.SUPABASE_ANON_KEY ||
      process.env.SUPABASE_KEY ||
      '',
  },
  images: { unoptimized: true },
};

export default nextConfig;
