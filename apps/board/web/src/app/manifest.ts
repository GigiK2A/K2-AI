import type { MetadataRoute } from "next";

export default function manifest(): MetadataRoute.Manifest {
  return {
    name: "K2-Board",
    short_name: "K2-Board",
    description: "Quadro operativo K2-AI",
    start_url: "/dashboard",
    display: "standalone",
    background_color: "#080808",
    theme_color: "#080808",
    icons: [
      { src: "/icon-192.png", sizes: "192x192", type: "image/png", purpose: "any" },
      { src: "/icon-512.png", sizes: "512x512", type: "image/png", purpose: "maskable" },
    ],
  };
}
