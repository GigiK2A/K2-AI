"use client";

import { usePathname } from "next/navigation";
import { navItems } from "./nav-items";

export function Header() {
  const pathname = usePathname();
  const active = navItems.find(i => pathname.startsWith(i.href));
  const title = active?.label ?? "Board";

  return (
    <header className="sticky top-0 z-20 h-14 border-b border-[color:var(--color-line)] bg-[color:var(--color-bg)]/95 backdrop-blur flex items-center px-4 md:px-6">
      <h1 className="text-base md:text-lg font-bold tracking-tight">{title}</h1>
    </header>
  );
}
