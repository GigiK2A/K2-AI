import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  basePath: '/app',
  assetPrefix: '/app',
  output: 'export',
  trailingSlash: true,
  images: { unoptimized: true },
};

export default nextConfig;
