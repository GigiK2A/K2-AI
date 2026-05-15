import type { NextConfig } from "next";

// In production the FastAPI backend runs in the same container on loopback at :8765
// (chosen to avoid collision with Railway's PORT, which often defaults to 8000/3000).
// In local dev set INTERNAL_API_URL=http://127.0.0.1:8000 to talk to a separately-launched uvicorn.
// NOTE: this value is baked into the build manifest, so changing it requires a rebuild.
const INTERNAL_API = process.env.INTERNAL_API_URL ?? "http://127.0.0.1:8765";

const nextConfig: NextConfig = {
  reactStrictMode: true,
  output: "standalone",
  async rewrites() {
    return [
      { source: "/api/:path*", destination: `${INTERNAL_API}/api/:path*` },
      { source: "/health", destination: `${INTERNAL_API}/health` },
    ];
  },
};

export default nextConfig;
