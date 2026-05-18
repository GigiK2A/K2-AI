import type { Metadata } from "next";
import "./globals.css";
import { Providers } from "./providers";

export const metadata: Metadata = {
  title: "K2-AI Bot",
  description: "Assistente AI premium per lead generation e report professionali",
  // basePath: '/app' — Next.js auto-icon discovery non sempre applica il prefisso
  // su tutti i browser. Dichiariamo esplicitamente i path completi.
  icons: {
    icon: [
      { url: "/app/icon.png", type: "image/png", sizes: "512x512" },
      { url: "/app/logo-k2ai.png", type: "image/png", sizes: "any" },
    ],
    shortcut: "/app/icon.png",
    apple: "/app/apple-icon.png",
  },
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="it">
      <body>
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
