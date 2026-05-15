import { redirect } from "next/navigation";
import { getCurrentUser } from "@/lib/auth";
import { LoginForm } from "@/components/auth/login-form";

export default async function LoginPage() {
  const user = await getCurrentUser();
  if (user) redirect("/dashboard");

  return (
    <main className="min-h-screen flex items-center justify-center bg-[color:var(--color-bg)] px-6">
      <div className="w-full max-w-sm">
        <div className="mb-8 text-center">
          <h1 className="text-3xl font-bold">K2-Board</h1>
          <p className="mt-2 text-sm text-[color:var(--color-text-soft)]">Quadro operativo</p>
        </div>
        <LoginForm />
      </div>
    </main>
  );
}
