import { BarChart3 } from "lucide-react";
import { Mode } from "@/types/chat";

export function ModeSwitcher({ mode, onChange }: { mode: Mode; onChange: (m: Mode) => void }) {
  return (
    <div>
      <button
        type="button"
        onClick={() => onChange("report")}
        className="flex w-full items-center gap-2 rounded-xl border border-[var(--teal)] bg-[var(--teal-soft)] px-3 py-2 text-left text-sm text-white"
      >
        <BarChart3 size={16} />
        Report Premium
      </button>
    </div>
  );
}
