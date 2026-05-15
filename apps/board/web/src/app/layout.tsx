import type { Metadata, Viewport } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "K2-Board",
  description: "Quadro operativo K2-AI",
  manifest: "/manifest.json",
};

export const viewport: Viewport = {
  themeColor: "#080808",
  width: "device-width",
  initialScale: 1,
  viewportFit: "cover",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="it">
      <head>
        <link
          rel="stylesheet"
          href="https://api.fontshare.com/v2/css?f[]=clash-display@700&f[]=dm-sans@400,500,600&display=swap"
        />
      </head>
      <body>{children}</body>
    </html>
  );
}
