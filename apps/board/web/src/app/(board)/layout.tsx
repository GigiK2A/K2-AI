import { requireUser } from "@/lib/auth";
import { Sidebar } from "@/components/nav/sidebar";
import { BottomNav } from "@/components/nav/bottom-nav";
import { Header } from "@/components/nav/header";

export default async function BoardLayout({ children }: { children: React.ReactNode }) {
  const user = await requireUser();
  return (
    <div className="flex min-h-screen bg-[color:var(--color-bg)]">
      <Sidebar username={user.username} />
      <div className="flex-1 flex flex-col min-w-0">
        <Header />
        <main className="flex-1 pb-20 md:pb-0">{children}</main>
        <BottomNav />
      </div>
    </div>
  );
}
