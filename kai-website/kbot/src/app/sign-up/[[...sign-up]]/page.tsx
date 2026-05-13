import { SignUp } from "@clerk/clerk-react";
import Image from "next/image";

const BULLETS = [
  {
    title: "Report strategici pronti in minuti",
    sub: "Analisi, KPI e piano operativo generati dall'AI",
  },
  {
    title: "Copertura multi-settore",
    sub: "PMI, hospitality, legale, compliance, edilizia, tokenizzazione",
  },
  {
    title: "Documento consegnabile al cliente",
    sub: "PDF professionale scaricabile, nessun lavoro manuale",
  },
];

const clerkAppearance = {
  variables: {
    colorPrimary: "#14b8a6",
    colorBackground: "#0a0a0a",
    colorInputBackground: "#111111",
    colorInputText: "#e5e7eb",
    colorText: "#e5e7eb",
    colorTextSecondary: "#6b7280",
    borderRadius: "8px",
  },
  elements: {
    card: { boxShadow: "none", border: "1px solid #1f1f1f", background: "#050505" },
    formButtonPrimary: { background: "#14b8a6", color: "#000", fontWeight: "700" },
    socialButtonsBlockButton: { border: "1px solid #1f1f1f", background: "#111111", color: "#ffffff" },
    socialButtonsBlockButtonText: { color: "#ffffff" },
    socialButtonsProviderIcon: { filter: "invert(1)" },
    dividerLine: { background: "#1f1f1f" },
    dividerText: { color: "#4b5563" },
    footerActionLink: { color: "#14b8a6" },
    headerTitle: { display: "none" },
    headerSubtitle: { display: "none" },
  },
};

export function generateStaticParams() {
  return [{ 'sign-up': [] as string[] }];
}

export default function SignUpPage() {
  return (
    <div className="flex min-h-screen bg-[#050505]">
      {/* LEFT PANEL — hidden on mobile */}
      <div
        className="hidden md:flex md:flex-1 flex-col justify-between p-12 relative overflow-hidden"
        style={{ background: "linear-gradient(160deg,#071f1d 0%,#050d0c 60%,#050505 100%)" }}
      >
        <div
          style={{
            position: "absolute",
            top: "-80px",
            left: "-80px",
            width: "300px",
            height: "300px",
            background: "radial-gradient(circle,rgba(20,184,166,0.12) 0%,transparent 70%)",
            pointerEvents: "none",
          }}
        />

        <div className="flex items-center gap-3 relative">
          <Image src="/logo-k2ai.png" alt="K2-AI" width={38} height={38} className="rounded-xl" />
          <span style={{ fontWeight: 800, color: "#fff", fontSize: "16px", letterSpacing: "0.5px" }}>
            K2-AI
          </span>
        </div>

        <div className="flex flex-col gap-6 relative">
          <div>
            <h1
              style={{
                fontSize: "28px",
                fontWeight: 800,
                color: "#fff",
                lineHeight: 1.25,
                marginBottom: "8px",
              }}
            >
              Fai crescere il tuo
              <br />
              business con l&apos;AI
            </h1>
            <p style={{ fontSize: "13px", color: "#6b7280", lineHeight: 1.5 }}>
              Report professionali e analisi strategica
              <br />
              generati in pochi minuti.
            </p>
          </div>

          <div className="flex flex-col gap-4">
            {BULLETS.map((b) => (
              <div key={b.title} className="flex items-start gap-3">
                <div
                  style={{
                    width: "22px",
                    height: "22px",
                    background: "rgba(20,184,166,0.15)",
                    border: "1px solid rgba(20,184,166,0.3)",
                    borderRadius: "6px",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    flexShrink: 0,
                    marginTop: "2px",
                  }}
                >
                  <span style={{ color: "#14b8a6", fontSize: "11px", fontWeight: 700 }}>✓</span>
                </div>
                <div>
                  <div style={{ fontSize: "13px", fontWeight: 600, color: "#e5e7eb" }}>{b.title}</div>
                  <div style={{ fontSize: "11px", color: "#6b7280", marginTop: "2px" }}>{b.sub}</div>
                </div>
              </div>
            ))}
          </div>
        </div>

        <div style={{ fontSize: "10px", color: "#374151" }} className="relative">
          © 2026 K2-AI — k2-ai.it
        </div>
      </div>

      {/* RIGHT PANEL */}
      <div
        className="flex flex-1 flex-col items-center justify-center p-6 md:p-12"
        style={{ background: "#0a0a0a", borderLeft: "1px solid #111" }}
      >
        <div className="flex md:hidden items-center gap-3 mb-8">
          <Image src="/logo-k2ai.png" alt="K2-AI" width={32} height={32} className="rounded-lg" />
          <span style={{ fontWeight: 800, color: "#fff", fontSize: "15px" }}>K2-AI</span>
        </div>

        <div className="w-full max-w-sm">
          <div className="mb-6 hidden md:block">
            <h2 style={{ fontSize: "20px", fontWeight: 700, color: "#fff", marginBottom: "4px" }}>
              Crea il tuo account
            </h2>
          </div>
          <SignUp appearance={clerkAppearance} />
        </div>
      </div>
    </div>
  );
}
