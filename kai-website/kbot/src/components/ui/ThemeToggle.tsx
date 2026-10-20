"use client";

import { useEffect, useState } from "react";
import { Moon, Sun } from "lucide-react";

type Theme = "dark" | "light";
const KEY = "kbot.theme";

function applyTheme(t: Theme) {
  if (typeof document === "undefined") return;
  if (t === "dark") {
    document.documentElement.setAttribute("data-theme", "dark");
  } else {
    document.documentElement.removeAttribute("data-theme");
  }
}

export function ThemeToggle({ className }: { className?: string }) {
  const [theme, setTheme] = useState<Theme>("light");
  const [mounted, setMounted] = useState(false);

  // Hydration-safe init: read localStorage on mount only, then apply theme.
  // SSR has no localStorage so we must defer to after-mount.
  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setMounted(true);
    try {
      const stored = (localStorage.getItem(KEY) as Theme | null) ?? "light";
      const initial: Theme = stored === "dark" ? "dark" : "light";
      setTheme(initial);
      applyTheme(initial);
    } catch {
      /* ignore */
    }
  }, []);

  function toggle() {
    const next: Theme = theme === "dark" ? "light" : "dark";
    setTheme(next);
    applyTheme(next);
    try {
      localStorage.setItem(KEY, next);
    } catch {
      /* ignore */
    }
  }

  if (!mounted) {
    // Render nothing on SSR — avoids hydration flash. Keeps default dark.
    return null;
  }

  return (
    <button
      type="button"
      onClick={toggle}
      aria-label={theme === "dark" ? "Tema chiaro" : "Tema scuro"}
      title={theme === "dark" ? "Passa al tema chiaro" : "Passa al tema scuro"}
      className={
        className ??
        "rounded-lg border border-[var(--line)] p-2 text-[var(--text-soft)] hover:border-[var(--line-strong)] hover:text-[var(--text-main)]"
      }
    >
      {theme === "dark" ? <Sun size={14} /> : <Moon size={14} />}
    </button>
  );
}
