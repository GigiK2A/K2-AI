"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { LogOut } from "lucide-react";
import { navItems } from "./nav-items";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? "";

export function Sidebar({ username }: { username: string }) {
  const pathname = usePathname();

  async function handleLogout() {
    await fetch(`${API_BASE}/api/auth/logout`, { method: "POST", credentials: "include" });
    window.location.href = "/login";
  }

  return (
    <aside className="hidden md:flex h-screen w-[220px] flex-col border-r border-[color:var(--color-line)] bg-[color:var(--color-bg-soft)] sticky top-0">
      <div className="flex h-14 items-center px-5 border-b border-[color:var(--color-line)]">
        <Link href="/dashboard" className="text-base font-bold tracking-tight">K2-Board</Link>
      </div>
      <nav className="flex-1 overflow-y-auto px-2 py-3">
        {navItems.map(item => {
          const active = pathname.startsWith(item.href);
          const Icon = item.icon;
          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "flex items-center gap-3 rounded-lg px-3 py-2 text-sm transition-colors",
                active
                  ? "bg-[color:var(--color-bg-elevated)] text-[color:var(--color-teal)] border-l-2 border-[color:var(--color-teal)] -ml-[2px] pl-[10px]"
                  : "text-[color:var(--color-text-soft)] hover:bg-[color:var(--color-bg-elevated)] hover:text-[color:var(--color-text)]"
              )}
            >
              <Icon size={16} />
              {item.label}
            </Link>
          );
        })}
      </nav>
      <div className="border-t border-[color:var(--color-line)] p-3">
        <div className="text-xs text-[color:var(--color-text-muted)] mb-2 px-2">@{username}</div>
        <Button variant="ghost" size="sm" className="w-full justify-start" onClick={handleLogout}>
          <LogOut size={14} /> Esci
        </Button>
      </div>
    </aside>
  );
}
