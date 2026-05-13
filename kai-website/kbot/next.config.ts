import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  basePath: '/app',
  assetPrefix: '/app',
  outputFileTracingRoot: process.cwd(),
  trailingSlash: true,
  images: { unoptimized: true },
};

export default nextConfig;
