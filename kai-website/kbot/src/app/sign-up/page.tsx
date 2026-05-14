import { AuthForm } from "@/components/auth/AuthForm";

export default function SignUpPage() {
  return (
    <main className="flex min-h-screen items-center justify-center bg-[#050505] px-6 py-10 text-white">
      <div className="w-full max-w-sm">
        <div className="mb-6">
          <div className="mb-4 flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-[#14b8a6] font-black text-black">K</div>
            <span className="text-sm font-extrabold tracking-wide">K2-AI</span>
          </div>
          <h1 className="text-2xl font-extrabold">Crea il tuo account</h1>
          <p className="mt-2 text-sm text-[#6b7280]">Registrati per accedere alla chat report premium.</p>
        </div>
        <AuthForm mode="register" />
      </div>
    </main>
  );
}
