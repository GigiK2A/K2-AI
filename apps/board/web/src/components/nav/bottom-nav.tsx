"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { MoreHorizontal } from "lucide-react";
import { primaryMobileItems, overflowMobileItems } from "./nav-items";
import { cn } from "@/lib/utils";
import { useState } from "react";

export function BottomNav() {
  const pathname = usePathname();
  const [moreOpen, setMoreOpen] = useState(false);

  return (
    <>
      <nav className="md:hidden fixed bottom-0 inset-x-0 z-30 border-t border-[color:var(--color-line)] bg-[color:var(--color-bg-soft)]/95 backdrop-blur">
        <div className="grid grid-cols-5 h-14">
          {primaryMobileItems.map(item => {
            const active = pathname.startsWith(item.href);
            const Icon = item.icon;
            return (
              <Link
                key={item.href}
                href={item.href}
                className={cn(
                  "flex flex-col items-center justify-center gap-0.5 text-[10px]",
                  active ? "text-[color:var(--color-teal)]" : "text-[color:var(--color-text-muted)]"
                )}
              >
                <Icon size={20} />
                <span>{item.label}</span>
              </Link>
            );
          })}
          <button
            onClick={() => setMoreOpen(v => !v)}
            className={cn(
              "flex flex-col items-center justify-center gap-0.5 text-[10px]",
              moreOpen ? "text-[color:var(--color-teal)]" : "text-[color:var(--color-text-muted)]"
            )}
          >
            <MoreHorizontal size={20} />
            <span>Altro</span>
          </button>
        </div>
      </nav>

      {moreOpen && (
        <div
          className="md:hidden fixed inset-0 z-40 bg-black/60"
          onClick={() => setMoreOpen(false)}
        >
          <div
            className="absolute bottom-14 inset-x-0 bg-[color:var(--color-bg-soft)] border-t border-[color:var(--color-line)] p-3"
            onClick={e => e.stopPropagation()}
          >
            <div className="grid grid-cols-4 gap-2">
              {overflowMobileItems.map(item => {
                const Icon = item.icon;
                return (
                  <Link
                    key={item.href}
                    href={item.href}
                    onClick={() => setMoreOpen(false)}
                    className="flex flex-col items-center gap-1 rounded-lg p-3 text-xs text-[color:var(--color-text-soft)] hover:bg-[color:var(--color-bg-elevated)]"
                  >
                    <Icon size={20} />
                    {item.label}
                  </Link>
                );
              })}
            </div>
          </div>
        </div>
      )}
    </>
  );
}
