import type { NextConfig } from "next";

// In production the FastAPI backend runs in the same container on loopback;
// in local dev it's the separately-launched uvicorn on :8000.
const INTERNAL_API = process.env.INTERNAL_API_URL ?? "http://127.0.0.1:8000";

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
